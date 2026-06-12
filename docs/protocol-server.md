# TCU ↔ server protocol

Protocol between the TCU and the telematics server (CARWINGS / OpenCARWINGS).
Primary source: the [opencarwings](https://github.com/developerfromjokela/opencarwings)
server code and the TCU firmware reverse engineering `[TO CONFIRM: cross-check
against the code before implementing]`.

> **Nothing in this document has been verified against the code or a real
> capture yet.** Phase 0 of the project is precisely about validating this
> document by making a Python client talk to OpenCARWINGS' `test_server.py`.

## Transport

- TCP, port **55230** `[TO CONFIRM: opencarwings code]`.
- Connection initiated by the TCU (outbound — no listening port on the vehicle
  side) `[TO CONFIRM]`.
- Transport-layer encryption: `[TBD — probably none in the original protocol;
  to be confirmed and compensated for (VPN/TLS) at deployment time]`.

## Packets

Known packet types: **1, 3 and 5** `[TO CONFIRM: opencarwings code]`.

| Type | Role | Format |
|---|---|---|
| 1 | `[TBD]` | `[TBD]` |
| 3 | `[TBD]` | `[TBD]` |
| 5 | `[TBD]` | `[TBD]` |

Endianness, framing (length-prefixed? delimiter?), checksums:
`[TBD: read the opencarwings code]`.

## Authentication

Password hash: **modified CRC-32** with the suffix **`"evtelematics"`**
appended to the password before hashing `[TO CONFIRM: opencarwings code —
check the exact concatenation order, the polynomial and any CRC inversions]`.

Identifiers transmitted (VIN? unit ID? IMEI?): `[TBD]`.

## Session lifecycle

`[TBD]` — hypotheses to validate in Phase 0:

1. TCP connect → handshake/auth.
2. Telemetry upload (periodic or event-driven?).
3. Command reception (polling? persistent connection? SMS wake-up on the
   original TCU?). The remote wake-up mechanism is critical for the design
   (standby power draw): `[TBD — high priority]`.

## To verify

- [ ] Port 55230 and TCP transport `[TO CONFIRM: opencarwings code]`
- [ ] Exact format of packet types 1/3/5 `[TBD]`
- [ ] Exact hash algorithm (modified CRC-32 + "evtelematics") `[TO CONFIRM]`
- [ ] Wake-up mechanism for remote commands `[TBD]`
- [ ] Behavior of `test_server.py` as a reference oracle `[TO CONFIRM]`
