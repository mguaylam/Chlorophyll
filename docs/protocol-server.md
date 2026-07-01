# TCU ↔ server protocol

Protocol between the TCU and the telematics server (CARWINGS / OpenCARWINGS).

Facts marked `[VERIFIED: opencarwings@3927dad]` were read directly from the
OpenCARWINGS source on 2026-06-11 (commit `3927dad`):
`tculink/gdc_proto/{parser,datafields,responses}.py`,
`tculink/management/commands/tcuserver.py`, `tculink/utils/password_hash.py`,
`tculink/sms/`. They describe **how OpenCARWINGS implements the protocol**;
agreement with the real TCU firmware is upstream's claim, to be exercised in
Phase 0 against `scripts/test_server.py` from nissan-leaf-tcu@1372ec9.

## Transport

- TCP, port **55230** `[VERIFIED: opencarwings@3927dad, tcuserver.py:516 +
  docker-compose.yml]`.
- Connection initiated by the TCU; the server only listens
  `[VERIFIED: opencarwings@3927dad — asyncio.start_server, no outbound
  connection to the TCU]`.
- No transport encryption in the server implementation — raw TCP
  `[VERIFIED: opencarwings@3927dad]`. Deployment should compensate (private
  APN, VPN, or TLS termination if the client adds it): `[TBD: deployment
  choice]`.
- Max packet size accepted by the parser: 1024 bytes
  `[VERIFIED: opencarwings@3927dad, parser.py]`.

## Remote wake-up: SMS

**The server wakes the TCU by SMS** when a command is issued: it sends the
text `NISSAN_EVIT_TELEMATICS_CENTER` to the TCU's SIM through a pluggable SMS
provider (Hologram, Monogoto, 46elks, SMS gateway, or manual sending), then
flags the command in the database. The woken TCU connects and receives the
command as the response to its INIT packet.
`[VERIFIED: opencarwings@3927dad — api/views.py:356, settings.example.py:189,
tculink/sms/]`

Whether the real TCU triggers on the SMS *content* or just on any SMS:
`[TO CONFIRM: nissan-leaf-tcu firmware]`. Design consequence: the replacement
modem must be able to receive SMS in standby (stay registered), or another
push channel must replace it — see [hardware.md](hardware.md).

## Packet types (TCU → server)

First byte of the packet = type `[VERIFIED: opencarwings@3927dad,
datafields.py]`:

| First byte | Type | Name | Role |
|---|---|---|---|
| 0x01 | 1 | INIT | Logon / command poll. Server answers with the pending command response, or a failure response if none. |
| 0x03 | 3 | DATA | Telemetry + event reports (EV info body). |
| 0x05 | 5 | CONFIG | TCU configuration dump (APN, DNS, server URL…). 597 bytes, skips auth check. |

### Common layout (types 1 and 3)

`[VERIFIED: opencarwings@3927dad, parser.py + datafields.py]`

| Offset | Size | Field |
|---|---|---|
| 0 | 1 | Packet type (0x01/0x03/0x05) |
| 1 | 1 | Vehicle descriptor: AZE0 sends **0x92**, ZE0 sends 0x02 |
| 4 | 4 | Vehicle codes 1–4 |
| 9..26 | 17 | VIN (ASCII, NUL-padded) |
| 27..39 | 12 | TCU ID (model) |
| 40..55 | 15 | MSN |
| 56..68 | 12 | Unit ID (navi serial) |
| 69..89 | 20 | ICCID (SIM) |
| 90..99 | 9 | TCU SW version |
| 100 | 1 | Body type |
| 101..118 | 18 | Environment block; GPS at offset 103 (flags byte, then lat/lon as deg/min/sec×100, big-endian) |
| 119..152 | 34 | Auth block: username at 120..135, password hash at 137..152 (ASCII, NUL-padded) |
| 153.. | var | Body (type 3): EV info bitfields |

Body types (byte 100) `[VERIFIED: opencarwings@3927dad]`: 0x27 logon,
0x28 charge_status, 0x29 cp_remind (charger unplugged), 0x2A remote_stop,
0x2B charge_result, 0x2C ac_result, 0x2E config_read, 0x2F battery_heat.

The type-3 EV info body carries SOC (×20), GIDs, SOH, charge state,
plugged-in, A/C state, gear/ignition, charge-time estimates, battery heater
and 6 kW OBC flags, packed as bitfields — exact bit layout in
`gdc_proto/datafields.py:parse_evinfo` `[VERIFIED: opencarwings@3927dad]`.

## Responses (server → TCU)

`[VERIFIED: opencarwings@3927dad, responses.py]` — big-endian `struct` packing:

- **Type 2 command response** (8 bytes): `02 00 <len:u16> <dest> 02 00
  <cmd_byte>` where `cmd_byte = (failure<<7) | (command<<4)`. Known
  destination/command pairs: charge status 0x28/0x01, charge request
  0x2B/0x02, A/C on 0x2C/0x03, A/C off 0x2C/0x04.
- **Config read request**: fixed `04 00 00 08 2E 00 00 00`.
- Server-side command codes: 1 = charge status, 2 = start charge, 3 = A/C on,
  4 = A/C off, 5 = config read, 6 = auth common dest.

## Authentication

`[VERIFIED: opencarwings@3927dad, password_hash.py + tcuserver.py]`

- Hash = **standard CRC-32** (reflected polynomial 0xEDB88320, init
  0xFFFFFFFF, final XOR) of `password + b"evtelematics"`, rendered as 8
  uppercase hex chars. So "modified CRC-32" really means: standard CRC-32 over
  a suffixed input.
- Password: max 16 chars, charset `[A-Za-z0-9-_=+@#?!]`.
- The server matches the car by **VIN**, then checks TCU ID, Unit ID (navi)
  and ICCID against the registered car, then username **or** password hash
  (`tcuserver.py:209` — an OR, not AND).
- Type 5 (CONFIG) packets bypass the auth check.

## Session lifecycle

`[VERIFIED: opencarwings@3927dad, tcuserver.py — server side]`

1. Wake (SMS, or own schedule) → TCU opens TCP to server.
2. TCU sends type 1 (INIT/logon) → server replies with the pending command
   response (charge/AC/config…) or `charge_status(False)` when none.
3. TCU executes and reports: type 3 packets with result bodies (ac_result,
   charge_result, remote_stop, battery_heat…), which also refresh telemetry
   and GPS; server pushes user notifications.
4. Connection closes; nothing persistent.

Upstream documentation adds: the real TCU waits specifically for the SMS text
`NISSAN_EVIT_TELEMATICS_CENTER`, then connects to the programmed server on
port 55230, sends INIT, and **times out after about 20–30 s** if no valid
command response arrives `[TO CONFIRM: nissan-leaf-tcu@1372ec9,
communication/README.md — upstream's analysis, not yet reproduced]`. The TCU
also has a separate "ACP SMS" channel (stolen-vehicle tracking, FOTA,
immobilizer) not analyzed upstream — out of scope for Chlorophyll.

Firmware strings confirm the TCU also reports **periodically**, with separate
intervals for ignition-on vs ignition-off (`AcpEvHisReporter`), not only on
command `[VERIFIED: firmware strings 06.42R — see firmware-findings.md]`. The
server port is read from provisioned config, not hardcoded, and the IP stack
is lwIP with TCP keepalive. Exact default intervals and retry behavior:
`[TO CONFIRM: disassembly / live capture]`.

## To verify (Phase 0)

- [x] Exercise a Python client against the upstream server code — **done**.
  Our `build_init_packet` / `build_data_packet` / `parse_response` output is
  run through the *actual* `opencarwings@3927dad` parser
  (`tculink/gdc_proto/parser.parse_gdc_packet`) and its response builders in
  `tools/tests/test_upstream_conformance.py`. Every field round-trips: VIN,
  tcu_id, unit_id, iccid, sw_version, vehicle descriptor (0x92), auth
  user + CRC-32 password hash, GPS lat/lon, and the EV-info body (SOC, GIDs,
  SOH, plug/charge/AC/ignition, range). The real server
  (`management/commands/tcuserver.py`) reads the whole socket buffer and calls
  `parse_gdc_packet(data)` directly with no length-framing, so parser-level
  conformance equals server-level acceptance
  `[VERIFIED: opencarwings@3927dad, conformance suite 2026-07-01]`.
- [x] Live end-to-end against `nissan-leaf-tcu/scripts/test_server.py` — **done,
  with one caveat**. A ZE0-descriptor INIT is accepted and answered with the
  hardcoded *Get Charge Status* response (`02 00 00 08 28 02 00 90`); the server
  decodes our VIN, tcu_id, unit_id, iccid and username correctly. **Caveat:**
  `test_server.py` gates on `data.startswith(b'\x01\x02\x00')`, i.e. it hardcodes
  byte[1] == 0x02 (a **ZE0** descriptor), so it silently drops our **AZE0**
  (0x92) packets. This is a limitation of that illustrative script, not of our
  builder — the opencarwings parser correctly treats byte[1] as the vehicle
  descriptor (`aze0 = byte_data[1] != 0x02`). `test_server.py` also slices
  `sw_version` at `[91:100]` and `pw_hash` at `[136:153]`, each one byte off
  from opencarwings' `[90:99]` / `[137:152]`, producing a dropped leading `0`
  and a spurious leading `\x00`; harmless (neither field is used for matching)
  but a reminder that **opencarwings `tcuserver` is the authoritative target**,
  not `test_server.py` `[VERIFIED: live run 2026-07-01]`.
- [ ] Run against a *live* OpenCARWINGS `tcuserver` (Django + DB), not just its
  parser, to confirm the full auth/command path end-to-end `[TO CONFIRM]`.
- [ ] Does the real TCU care about the SMS content? `[TO CONFIRM: firmware]`
- [ ] Real TCU session timing (socket lifetime, retries, periodic reports)
  `[TO CONFIRM]`
- [ ] GPS block exact offsets vs a real capture `[TO CONFIRM]`

**Conformance harness.** The checks above are reproducible from the repo:

```
git clone https://github.com/developerfromjokela/opencarwings      # 3927dad
git clone https://github.com/developerfromjokela/nissan-leaf-tcu    # test_server
cd tools
CHLOROPHYLL_OPENCARWINGS_DIR=…/opencarwings \
CHLOROPHYLL_NISSAN_LEAF_TCU_DIR=…/nissan-leaf-tcu \
    .venv/bin/python -m pytest tests/test_upstream_conformance.py -v
```

Without the env vars the suite stays hermetic (those tests skip).
