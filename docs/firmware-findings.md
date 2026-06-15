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

## Decompilation findings (Ghidra)

Done with Ghidra 12.1.2 headless on `application.bin`. Load base determined as
**`0xA0020000`** by correlating 32-bit literal-pool words against string offsets
(5183 hits vs 478 for the next candidate — a 10x margin)
`[VERIFIED: derived from literal-pool↔string correlation]`. Language
`ARM:LE:32:v5t`. Functions below are named by the FW debug strings they
reference.

### app → S12: the `requestCanAction` IPC message

`EvAcApp: send can active to S12` decompiles (`@0xA02F502C`) to an IPC send of a
**6-byte message**, not a CAN write:

- opcode byte **`0x85`**, an **active/inactive flag** (`1` = active), plus
  parameters and a status byte, sent via `requestCanAction - send via IPC`
  to the S12; on failure logs `requestCanAction - sendMessage failed`.
- Each EV app has its own active/inactive pair: `EvAcApp`, `EvChargeApp`,
  `EvChargeStatusApp`, `EvPluginRmdApp`.

`[VERIFIED: Ghidra decomp @0xA02F502C — 6-byte IPC msg, opcode 0x85, active
flag]`. This confirms the architecture: the app issues **high-level CAN-action
requests** to the S12; it never names raw CAN IDs. So the IDs stay in the S12,
which is not in this dump (see below).

### S12 → app: status notification channel

`@0xA0438600` is a dispatcher over a subtype byte for status the S12 pushes
back: `Sensor 1/2`, `HSD1_S12_STATUS` / `HSD2_S12_STATUS` (high-side driver
outputs), `DIG_OUT_S12_STATUS`, `HVAC_ON_STATUS`
`[VERIFIED: decomp @0xA0438600]`. This is the **GPIO / power-output / HVAC
state** channel — not the rich battery telemetry (SOC/GIDs), which travels as a
data response to a CAN-action request on a different path `[TO CONFIRM:
deeper decomp]`.

### Reporting intervals — units confirmed, defaults not in code

`AcpEvHisReporter::onCodingSrvCodingChanged` (`@0xA02947E0`) reads each value
from the coding store and applies fixed unit conversions
`[VERIFIED: decomp @0xA02947E0]`:

- `repInterval*`: coding value **× 60** → stored as seconds, so the coding is in
  **minutes**.
- `repTimeoutFact`: **× 1000** → seconds to milliseconds.
- `perWakeupTime`: a `ushort`, used directly.

The **default numeric values are not in the binary** — they live in the
coding/NVM partition and are read at runtime `[TBD: coding/NVM partition, not in
application.bin]`.

### The S12 firmware is not in this dump, and the host can't flash it

The host only ever talks to the S12 over IPC and writes a few **EEPROM
parameters** (`Write First LogZone to S12`, `Re-Initial S12 EEPROM and write
Signature`, HW part number / version / programming date). There is **no S12
application image and no S12 flashing/download routine** in the dump; the lone
`reflash` string is the baseband's own recovery mode
(`RecoverySrv:: enter reflash mode, stop GSM/GPRS`)
`[VERIFIED: strings + decomp]`. Consequence: the S12's CAN IDs and bitrate
cannot be recovered from the published dump — only by reading the S12 chip
itself (hardware, likely flash-secured) or by **live CAN sniffing** (the
practical path).

## Toolchain

Ghidra 12.1.2 headless is set up locally (`~/ghidra`, JDK 25) and driven from
scripts (`tools/ghidra_scripts/XrefDecompile.java`: keyword → string xref →
decompile). The Ghidra project lives under `tools/ghidra_proj/` (gitignored —
it embeds the proprietary binary). Capstone is also available for quick
disassembly without a full Ghidra import.

## What would still need deeper work

- The **EV telemetry data path** (how SOC/GIDs/SOH come back from the S12) —
  partially mapped; the rich-data response handler is not yet decompiled `[TBD]`.
- Corroboration of the exact GDC body bit-packing against the encoder `[TBD]`.
- The `+XNAD` navi handler (Phase 2) — functions captured, not yet analyzed
  `[TBD]`.
