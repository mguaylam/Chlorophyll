# tools/

Host-side tooling. Python ≥ 3.11, code and comments in English.

## `carwings/` — CARWINGS protocol client (Phase 0)

An original Python implementation of the **TCU side** of the CARWINGS
protocol, derived from reading the OpenCARWINGS server source
(opencarwings@3927dad). It builds the binary packets a TCU sends and parses
the server's responses. See
[docs/protocol-server.md](../docs/protocol-server.md) for the byte layout and
its verification status.

```
carwings/
├── crc.py        # password hash (CRC-32 over password + "evtelematics")
├── protocol.py   # packet build/parse: INIT (type 1), DATA (type 3), responses
└── client.py     # TcuClient: TCP socket that impersonates a TCU
tests/            # pytest: hash vectors + packet round-trip
examples/
└── fake_tcu.py   # connect to a server and run a logon + telemetry
```

### Run the tests

```bash
cd tools
python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest
```

### What Phase 0 validated (2026-06-11)

- **Password hash**: matches OpenCARWINGS for known vectors
  (`""` → `5E90EF87`, `test` → `5F53E6C7`, …).
- **Packet framing**: against `nissan-leaf-tcu/scripts/test_server.py`, a ZE0
  logon (`01 02 00…`) is recognized and answered with the exact
  `02 00 00 08 28 02 00 90` "charge status" response, which our parser decodes
  correctly. (test_server keys on the ZE0 prefix only, so an AZE0 packet
  `01 92 00…` is received but not auto-answered — expected, not a bug.)
- **Authoritative decode**: our AZE0 INIT and DATA packets, fed through the
  real `opencarwings.tculink.gdc_proto.parser.parse_gdc_packet`, decode back
  to the exact identity (VIN, TCU ID, unit ID, ICCID, SW version, username,
  password hash), GPS fix, and telemetry (SOC, GIDs, SOH, plug/charge/AC
  flags) we encoded.

### Try it against a live server

```bash
# Terminal 1 — reference server from the nissan-leaf-tcu repo:
python nissan-leaf-tcu/scripts/test_server.py
# Terminal 2:
cd tools && PYTHONPATH=. .venv/bin/python examples/fake_tcu.py 127.0.0.1 55230
```

Or point `fake_tcu.py` at a local OpenCARWINGS `tcuserver` with a registered
car's identity to see telemetry appear in its UI.

### Known limits / TODO

- The EV-info body encoder covers the high-value fields; charge-time
  estimates and battery-heater bits are left zeroed until checked against a
  real capture `[TBD]`.
- No remote-command execution (no modem/SMS) — that is Phase 1.

## Possible later additions

- EV-CAN log decoder (candump → telemetry).
- USB capture analyzer for the `+XNAD*` link (Phase 2).
