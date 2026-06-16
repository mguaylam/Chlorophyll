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
- Modem (NAD = Network Access Device) wake budget is itself coded:
  `CODING_ID_POW_MAX_NAD_ACTIVATIONS` (a cap on how many times the modem may
  be woken) and `CODING_ID_POW_NAD_ALWAYS_ON_MAX_TIME` (logged in **minutes**)
  `[VERIFIED: decomp @0xA02E6A50]`. So the factory design explicitly bounds
  modem-on time and wake count to protect the 12V battery — the same trade-off
  Chlorophyll faces between SMS-reachability and standby drain.

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

### The app ↔ S12 IPC catalog (the factory feature map)

The application processor never touches CAN; it exchanges fixed **6-byte IPC
messages** with the S12, sent through one transport call
`FUN_a038E90C(ipcHandle, channel=4, buf, len=6)` `[VERIFIED: decomp]`. The first
byte is an **opcode**, and one byte (`struct+0x84`) is a rolling **sequence
counter** echoed in the S12's reply. This catalog is the authoritative list of
what the factory TCU can drive/observe — Chlorophyll's feature checklist for what
to wire to EV-CAN, even though we won't replicate the IPC itself.

**App → S12 (requests):**

| Opcode | Message | Payload | Source |
|---|---|---|---|
| `0x85` | `requestCanAction` | `actionType` (16-bit) + **active/inactive flag** (`1`=active) + seq | `@0xA02CC214` / `@0xA02F502C` |
| `0x8F` | `resendCarVolt2S12` | 12 V **car voltage** (2 B) + seq — power-mgmt handshake | `@0xA02C31AC` |

Each EV feature issues a `0x85` with its own active/inactive pair:
`EvAcApp` (remote A/C), `EvChargeApp` (charge), `EvChargeStatusApp`,
`EvPluginRmdApp` (plug-in reminder) `[VERIFIED: strings + decomp]`. Other IPC
services seen (not all byte-decoded): immobilizer (`Immo Block`=1 / `Unblock`=2 /
`ImmoStatus`=9, `IpcSrvImmobilizer`), GPS-speed report (`gpsSpeedReport`), and
S12 management (`Get S12 Version`, `Write First LogZone to S12`, `Re-Initial S12
EEPROM and write Signature`) `[VERIFIED: strings]`.

**S12 → app (notifications):** dispatcher `@0xA0438600` switches on **`byte[2]`
(subtype)**, each carrying `TID` + `Para` `[VERIFIED: decomp @0xA0438600]`:

| subtype | Notification |
|---|---|
| 1 | `Sensor 1` |
| 2 | `Sensor 2` |
| 3 | `HSD1_S12_STATUS` (high-side driver 1) |
| 4 | `HSD2_S12_STATUS` (high-side driver 2) |
| 5 | `DIG_OUT_S12_STATUS` (digital output) |
| 6 | `ITM_5V_DET_STATUS` (5 V detect) |
| 7 | `HVAC_ON_STATUS` |
| 0 / other | "Invalid sensor or GPIO message" |

This is the **GPIO / power-output / HVAC state** channel — not the rich battery
telemetry (SOC/GIDs), which comes back as a data response to a `0x85` request on a
different path `[TO CONFIRM: deeper decomp]`. Separately, an **S12 state report**
(`@0xA03F795C`) decodes `byte[5]`: **bit 4 = "stay awake, CAN active"**, **bit 5 =
"stay awake, diag active"** — how the S12 tells the baseband why it is being kept
awake `[VERIFIED: decomp @0xA03F795C]`. The car-voltage path is ACK'd by the S12
with a matching `Seq` (`ipcSrvPowerCarVoltSend` Idle/Resend/Run state machine)
`[VERIFIED: strings]`.

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

### CARWINGS authentication — and why our client already covers it

The dump has two distinct authentication mechanisms. Only the first is required
to interoperate with OpenCARWINGS.

**1. Mandatory: connect-time password + in-message PIN/PWD block.** The outgoing
auth block is built by `fill authentication` (`@0xA02D1394`): a flags byte, then
a **16-byte PIN** and a **16-byte PWD** field (each length-prefixed)
`[VERIFIED: decomp @0xA02D1394]`. This is the layer our Phase-0 client already
produces — the CRC-32 password hash (`password + "evtelematics"`) plus the
user/pass auth block (`tools/carwings`, `AUTH_OFFSET`), **validated against
OpenCARWINGS for known vectors**.

**2. Optional: per-message HMAC integrity (`isAuthOK`, `@0xA02ECE70`).** A
**two-stage keyed-hash** scheme `[VERIFIED: decomp @0xA02ECE70]`:

- *Stage 1 (session-key derivation):* `HMAC(authKey[20 B], nonceBlock[14 B]) →
  sessionKey[32 B]`. The 14-byte block is assembled from server/client nonce
  material (`clientNonce`, `NextNonce`, `Failed to generate server nonce`); a
  constant `0x7DA` (= 2010) is mixed in.
- *Stage 2 (message MAC):* `HMAC(sessionKey[32 B], messageBody) → tag`; the **first
  8 bytes** are compared (`ksr` received vs `ksc` computed).
- The 32-byte outputs point to a **SHA-256-family** primitive `[TO CONFIRM:
  exact hash — output size says SHA-256, not yet pinned]`. The whole layer is
  gated by `ENABLE_AUTHENTICATION` and a build flag (`Get/Set Authentication Key
  is not supported in this build!`) `[VERIFIED: strings]`.

**Conclusion for Chlorophyll:** the per-message HMAC is **not required** by
OpenCARWINGS — the Phase-0 client connects and exchanges INIT/DATA with only the
CRC-32 password + PIN/PWD block, no session key, no HMAC. So Phase 1 needs **no
session-key derivation and no HMAC implementation** `[TO CONFIRM: that the server
never enforces HMAC in any mode — strong evidence is the working client, not a
server-code audit]`. This removes crypto from the Phase-1 critical path.

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
