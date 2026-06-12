# Firmware findings (strings analysis)

What the published TCU firmware dump does and does not tell us. Derived by
running `strings` on the original firmware locally (not redistributed here).

## What was analyzed

- Source: `nissan-leaf-tcu@1372ec9`, `firmware-06.42/application.bin`.
- Target: the **PMB8876 baseband / application processor** (ARMv5t,
  little-endian) `[VERIFIED: firmware/README.md + binary strings]`.
- Software version **06.42R** — the same SW version as this project's unit.
  Caveat: the dump is the **MY2013 EU** variant; our unit is **MY2015 NAM**.
  The application code is likely near-identical, but region/year differences
  are possible `[TO CONFIRM]`.

## The decisive answer for EV-CAN

**The raw EV-CAN frame IDs are not in this dump.** The application processor
does not touch the CAN bus directly — it delegates to a separate
**MC9S12X ("S12")** companion MCU and only sends it high-level signals:
strings like `EvAcApp: send can active to S12`, `Get S12 Version`,
`DIG_OUT_S12_STATUS notification`, `Powering down via PIC/S12`
`[VERIFIED: firmware strings]`. The S12 firmware (which holds the actual CAN
IDs and bitrate) is **not** part of this dump. So firmware strings cannot
shortcut the EV-CAN sniffing in [evcan-telemetry.md](evcan-telemetry.md).

## What the firmware does reveal (useful)

### Power & wake architecture — directly informs the <5 mA goal

The original TCU keeps the big baseband asleep and relies on a small
always-on controller (S12/PIC) for power management and wake-up
`[VERIFIED: firmware strings]`:

- `ACC Service: enableWakeUPInterrupt` / `setWakeUpThreshold` — wakes on the
  ACC line (M67 pin 3).
- `CODING_ID_POW_PERIODIC_WAKUP_TIME`, `perWakeupTime=%d` — a configurable
  periodic wake-up timer.
- `AT+XPOW=[<mode>],[<timeout>],[<num_sp>]` — modem sleep/power control.
- `BAT_UNDERVOLTAGE_TEST_INTERVAL_FACTOR` — periodic 12V undervoltage check.

Design lesson for Chlorophyll: mirror this — ESP32-S3 in deep sleep, woken by
(a) ACC interrupt, (b) a periodic timer, (c) modem RI on inbound SMS — rather
than staying awake. See [hardware.md](hardware.md).

### Periodic reporting model

`AcpEvHisReporter::isTimeToSend` uses a periodic tick with **separate report
intervals for ignition-on vs ignition-off** (`repIntervalIgnOn`,
`repIntervalFactIgnOff`, `repTimeoutFact`) `[VERIFIED: firmware strings]`. So
the TCU reports telemetry periodically (configurable), not only on command —
this qualitatively answers the open "reporting cadence" question in
[protocol-server.md](protocol-server.md). Exact default values: `[TO CONFIRM —
would need disassembly of the coding defaults]`.

### Configuration provisioning

APN, DNS, GPRS username/password, server IP and **port** are provisioned and
stored in NVM/coding, partly via an SMS "second message"
(`AcpSmsClient::procSecondSms: received apn/DNS/gprs username`) and read back
at connect time (`ConnSrv::getPortNumber`, `get server port number`)
`[VERIFIED: firmware strings]`. This is why **55230 is not hardcoded** in the
binary — it comes from config — and it matches the type-5 CONFIG packet we
decoded (APN/DNS/server_url fields). The replacement can hardcode its own
server instead.

### Other confirmations

- Platform is Continental **"Novanto"**, with a Novanto→Nissan **DTC mapping**
  layer `[VERIFIED: firmware strings: "Novanto DTC %x is converted to NISSAN
  DTC %x"]`.
- TCP/IP via **lwIP**, with TCP keepalive in use (`TCP_KEEPALIVE`) — relevant
  to how long sessions stay open `[VERIFIED: firmware strings]`.
- Modem AT command set (proprietary `+X` family): `XPOW`, `XDNS`, `XGPRS*`,
  `XMUX`, `XREGNWI`, `XSERVICE`, `XSIMSTATE`, plus the `XNAD*` navi family
  already inventoried `[VERIFIED: firmware strings]`.
- A device-management server `http://63.84.202.21/mvpdm/...` appears
  (historical, almost certainly dead) `[VERIFIED: firmware strings]`.
- EV application modules map 1:1 to the GDC body types: `EvAcApp`,
  `EvChargeApp`, `EvChargeStatusApp`, `EvPluginRmdApp`, `EvStopRmdApp`,
  `EvConfigApp` `[VERIFIED: firmware strings]`.

## What would need disassembly (not strings)

The binary is ARMv5t LE, so Ghidra/objdump could in principle recover:

- The **app↔S12 internal message format** — which EV data points the app
  requests from the CAN MCU. This could *indirectly* reveal what telemetry
  exists, though still not the raw CAN IDs `[TBD]`.
- Default coding values (report intervals, wake times) `[TBD]`.
- Corroboration of the exact GDC body bit-packing `[TBD]`.

These are heavier tasks; none are blocking for Phase 0/1.
