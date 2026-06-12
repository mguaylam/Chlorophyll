# Architecture

Overview of the replacement TCU and its four interfaces.

## Role of the original TCU

The original TCU (type GNOV1N, SW 06.42R, HW 95048, made by Continental)
`[VERIFIED: owner's unit label]` provides:

- the 2G cellular link to the CARWINGS/NissanConnect servers
  `[TO CONFIRM: nissan-leaf-tcu repo]`;
- telemetry upload (SOC, charging, position) `[TO CONFIRM]`;
- reception of remote commands (pre-heating/cooling, charge start)
  `[TO CONFIRM]`;
- services shown on the navigation unit through an internal USB link
  `[TO CONFIRM: nissan-leaf-tcu repo]`.

## The four interfaces of the replacement

### 1. Power (M67 connector)

Permanent 12V battery feed (B+), ground, ACC and IGN signals on M67 terminals
1/2/3/4 `[VERIFIED: 2015 Leaf NAM SM, AV-538/AV-590]`. Details and pinout:
[pinout.md](pinout.md). Key constraint: standby power draw compatible with
the small 12V battery — see [hardware.md](hardware.md).

### 2. Vehicle bus (EV-CAN)

The TCU sits on the EV-CAN, available directly on **M67 terminals 9 (CAN H)
and 10 (CAN L)** `[VERIFIED: 2015 Leaf NAM SM, AV-538]` — so power, ignition
sensing and the vehicle bus all come through the one connector the original
TCU already uses. Frame IDs to read for telemetry (VCM / HVBAT / OBC), the
bitrate, and the listen-only verification plan are in
[evcan-telemetry.md](evcan-telemetry.md); all candidate IDs are still
`[TO MEASURE: sniff at M67]`.

### 3. Cellular (LTE)

The 2G modem is replaced by an LTE Cat-1 modem (see [hardware.md](hardware.md)).
Outbound TCP connection to the OpenCARWINGS server, port 55230
`[TO CONFIRM: opencarwings code]`. Protocol: [protocol-server.md](protocol-server.md).
Whether the original antenna (M113 connector) is reusable: `[TBD — 2G vs LTE
bands]`.

### 4. Navigation unit (USB, M68 connector)

USB 1.0 link between the TCU and the AV unit, driven by AT `+XNAD_*` commands
`[TO CONFIRM: nissan-leaf-tcu repo]`. Details: [protocol-navi-usb.md](protocol-navi-usb.md).
Phase 2 only; phases 0–1 do not depend on it.

## Phase breakdown

| Phase | Interfaces used | Hardware required |
|---|---|---|
| 0 | None (Python client ↔ test_server.py) | None |
| 1 | Power + EV-CAN + LTE | ESP32-S3, CAN transceiver, LTE modem |
| 2 | + navi USB | + USB OTG (native on ESP32-S3) |

## Design principle

The replacement TCU is **passive by default**: it listens to the EV-CAN and
only transmits frames for explicitly requested commands (A/C, charge). Any
transmitting behavior must be validated with the vehicle parked before any
real-world test.

## To verify

- Does the original TCU transmit on the EV-CAN, or is it purely passive?
  `[TBD: sniff the bus with the original TCU in place]`
- Does the AV unit tolerate the TCU being absent from the USB link (graceful
  degradation)? `[TO MEASURE: unplug M68 and observe]`
- Does removing the original TCU raise DTCs at the VCM? `[TBD]`
