# TCU ↔ navigation unit protocol (USB)

Internal link between the TCU and the AV (navigation) unit. **Phase 2**
(research) only.

> The **command/protocol layer is recoverable from the firmware** (the USB CDC
> stack and the `+XNAD` AT logic live in this baseband dump, unlike the CAN
> code) and is now partly decompiled — see "Recovered command grammar" below.
> The **physical/electrical layer** (USB speed, pinout, binary descriptors)
> still needs a capture `[TO MEASURE]`. Sources: firmware-06.42 decompilation +
> [nissan-leaf-tcu](https://github.com/developerfromjokela/nissan-leaf-tcu).

## Physical layer

- USB **1.0** (low/full speed: `[TBD]`) through the M68 connector
  `[TO CONFIRM: service manual]`. Pinout: [pinout.md](pinout.md).
- **The USB peripheral is integral to the TCU's baseband SoC** (Infineon
  PMB8876 / **SGOLD2**), not a separate chip: the firmware carries the full USB
  stack (`3p_usb_ems/.../physical/arch/sgold/...`) `[VERIFIED: firmware strings
  + decomp]`. The original TCU unified cellular + USB-to-navi + GPS in one SoC,
  while the S12 did CAN. In Chlorophyll these split: the navi USB is driven by
  the **ESP32-S3 native USB OTG**, cellular by the separate LTE modem.
- USB role: the firmware uses the USB **function** (device) HAL
  (`usb/func/hal/...`), so the **TCU is the USB device and the AV unit is the
  host** `[TO CONFIRM: firmware uses the device-side stack — confirm with a
  capture]`. Consequence: the ESP32-S3 must act as a USB **device**, not host.
- USB class: **CDC** (virtual serial), exposed as `USBCDC` with two ports
  (`/USBCDC/0`, `/USBCDC/1`) `[VERIFIED: firmware strings — USBCDC device]`.
  The `+XNAD` AT traffic rides over this CDC link `[TO CONFIRM: which of the two
  CDC ports]`.
- **Logical-channel routing is configurable (`+XSIO`)**: the firmware multiplexes
  three logical channels — **AT**, **Trace**, **Other** — onto the physical ports
  (`UART0..2`, `USB0`, `USB1`) per a numbered variant table, e.g.
  `Variant=0: AT=UART0,USB1; Trace=USB0; Other=UART1,UART2` …`Variant=5: AT=USB0,USB1`
  `[VERIFIED: firmware strings, 7 variants]`. A port-name→index resolver
  (`@0xA037F9B8`) maps the configured name to a slot: `/USBCDC/0`→0, `/USBCDC/1`→1,
  `/app/1`→2, else 3 `[VERIFIED: decomp @0xA037F9B8]`. So **which CDC port carries
  the navi AT traffic is set by coding, not hardwired** — the active `+XSIO`
  variant must be read from a live unit `[TO MEASURE: +XSIO? on a running TCU]`.
- **USB stack = a generic Comneon/Infineon function stack**, partly recoverable:
  - **String descriptors are in the dump** (UTF-16LE, data section
    `@~0x54B180`): Manufacturer **`Comneon GmbH`**, Product
    **`Comneon: 2 CDC and 1 MS.`**, and interface strings `CDC Communication
    Interface`, `CDC Data Interface`, `CDC Communication-only Interface`, `Trc`
    `[VERIFIED: UTF-16LE strings]`.
  - **Interface composition is therefore known: 2 × CDC + 1 × Mass Storage**
    (consistent with `/USBCDC/0`, `/USBCDC/1` and `USBIfc0..5`)
    `[VERIFIED: product string]`. So the device is a **CDC composite**, not a
    Nissan-bespoke class.
  - **The numeric descriptors (VID/PID, bcdUSB, endpoint map) are built in code,
    not stored as a blob**: a byte scan for a static device descriptor
    (`0x12 0x01`, even with composite-class / valid-`bMaxPacketSize` /
    `bNumConfigurations==1` constraints) finds **none**
    `[VERIFIED: binary scan, 0 hits]`. They are immediates in the descriptor
    builder (reached via a pointer table, so a string-xref does not land on it).
    The exact **VID/PID remain `[TO MEASURE: USB capture]`** — though, being a
    Comneon reference stack, they are likely the Comneon/Infineon defaults rather
    than Nissan-specific.

## Command layer

The **`+XNAD*`** AT command family exists in the TCU firmware
`[VERIFIED: strings of firmware-06.42 application.bin (nissan-leaf-tcu@1372ec9),
69 occurrences, extracted locally on 2026-06-11]`. **Which transport carries
them (the navi USB link vs an internal baseband↔CPU interface) is NOT
established**: `[TO CONFIRM — the strings prove the commands exist, not where
they travel]`.

Inventory extracted from the firmware strings (names only; parameters and
semantics `[TBD]`):

| Command group | Members | Assumed role |
|---|---|---|
| `+XNAD_DCM_Params_*` | `VIN`, `DCM_ID`, `DCM_VER`, `NAVI_ID`, `EV_SVC`, `CHG_HIST`, `PRE_AC_HIST` | Identity/config exchange (VIN, unit IDs, EV service settings, histories) `[TO CONFIRM]` |
| `+XNAD_DICCIDSER` | — | SIM ICCID report `[TO CONFIRM]` |
| Call control | `+XNAD_Ecall_*`, `+XNAD_ACNcall_*`, `+XNAD_servicecall_*` (each: `start_request`, `end_request`, `go_to_voice`, `go_to_data`) | eCall / automatic collision notification / operator call session control `[TO CONFIRM]` |
| `+XNAD_NAVI_Info_sent` | — | Navi data handshake `[TO CONFIRM]` |
| Modem/system | `+XNADFS`, `+XNADFOTA`, `+XNADTRACE`, `+XNADPIDAT`, `+XNADPIDCTRL`, `+XNADPWRCNT` | Filesystem, OTA update, tracing, power control `[TO CONFIRM]` |

Observed syntax patterns in the strings: `AT+XNADFS=`, `AT+XNADFS?`,
`+XNAD_DCM_Params_EV_SVC:(0,1),(0-1440),(0,1)` (test form with ranges) —
consistent with a standard AT command grammar
`[VERIFIED: firmware strings]`.

## Recovered command grammar (decompiled)

The exact AT response grammar and parameter formats, recovered from the dump
`[VERIFIED: firmware strings + decomp @0xA033B654 / @0xA033B668]`:

| Response string | Payload format | Source param (coding ID) |
|---|---|---|
| `+XNAD_DCM_Params_VIN:"%s"` | VIN, 17 bytes (0x0F = unset/fill) | `0x29` (17 B) |
| `+XNAD_DCM_Params_DCM_ID:"%s%s"` | two concatenated parts | `0x5B` (4 B) + `0x5A` (8 B) |
| `+XNAD_DCM_Params_DCM_VER:"%s000%02d%02d"` | SW version + two BCD-ish fields | — |
| `+XNAD_DCM_Params_NAVI_ID:"%s"` | navi/unit ID, 14 bytes | `0x27` (14 B) |
| `+XNAD_DCM_Params_EV_SVC:%d,%d,%d` | enable, interval **0–1440 min** (≤24 h), enable | coding |
| `+XNAD_DCM_Params_CHG_HIST:%d` (`=(0-3)`) | charge-history mode 0–3 | coding |
| `+XNAD_DCM_Params_PRE_AC_HIST:%d` | pre-A/C history | coding |
| `+XNAD_DICCIDSER:"%s"` | SIM ICCID | — |
| `+XNAD_NAVI_Info_sent:(0,1),(0,1),(YYYYMMDDHHMMSS)` | two flags + timestamp (2000–2300 range) | — |

Behavior: the navi (USB host) queries; the TCU reads the value from coding/NVM
via a parameter accessor (`obj->fn[0x90](id, buf, len)`) and replies with the
AT string, setting a result code — **1 = OK, 2 = error**
`[VERIFIED: decomp @0xA033B654]`. Call-control commands (`+XNAD_Ecall_*`,
`+XNAD_ACNcall_*`, `+XNAD_servicecall_*`: `start_request` / `end_request` /
`go_to_voice` / `go_to_data`) have their own handlers
`[VERIFIED: decomp @0xA02CDDE4]`.

What this means for emulation: the application protocol the ESP32-S3 must speak
to satisfy the navi is **largely recoverable from the dump without hardware** —
remaining unknowns are the framing details and the physical layer, not the
command vocabulary.

## Decompilation note (Ghidra)

Decompiling the `+XNAD` references (SW 06.42R) confirms `XNAD` is a substantial
subsystem with its own task and mailbox (`XNAD_TASK`, `XNAD_mbox`,
`XNADAT_INFO_IND`) `[VERIFIED: decomp]`. The call-control commands are **real
handlers**, not just format strings: `+XNAD_Ecall_*`, `+XNAD_ACNcall_*`,
`+XNAD_servicecall_*` each have `start_request` / `end_request` /
`go_to_voice` / `go_to_data` handling decompiled at `@0xA02CDDE4` and around
`@0xA02F606C..0xA02F9834` `[VERIFIED: decomp]`. There are also
`+XNADPIDAT:` / `+XNADPIDCTRL:` handlers (`@0xA0309644`, `@0xA03098F8`).

This still does **not** resolve the transport question (USB to the AV unit vs an
internal baseband interface): `NAD` = Network Access Device (the modem side), so
part of the `+XNAD` family is clearly modem/eCall control, while
`+XNAD_DCM_Params_*` / `+XNAD_NAVI_Info_sent` may be the AV-unit-facing part. The
split between "to the navi" and "to the modem" remains `[TO CONFIRM:
USB capture]`.

## What the TCU does for the navi — and what it does NOT

Decompiling the navi data path settles the scope question: **rich content
(Google/POI search, charging-station lists, weather, traffic) does not pass
through this TCU and is not in the dump** — a strings sweep finds no such handlers
`[VERIFIED: strings — 0 content handlers]`. That content is handled by the
**navigation unit's own software** talking to the server; the TCU plays only two
roles:

1. **Position reporter (navi → TCU → server).** `EvAcpHandler` (`@0xA02F3A10`)
   parses `navi info` from the AV unit — `position`, `datum`, `home`,
   `latitude`/`longitude` (mode/deg/min/sec) with range validation (lat ≤ 90°,
   minutes ≤ 60, lon ≤ 180) — and the report builder (`@0xA02D1DE0`) assembles a
   CARWINGS message: *vehicle descriptor + destination + source + time stamp +
   navi position + authentication* `[VERIFIED: decomp @0xA02F3A10, @0xA02D1DE0]`.
2. **Data bearer / NAD (Network Access Device).** The navi opens its own IP
   session *through* the TCU's modem: `BspNwaDial` returns `IP/DNS1/DNS2`, APN and
   carrier parameter sets (1–15) are coded, and `+XNAD` literally means Network
   Access Device `[VERIFIED: strings + decomp]`.

**Design consequence (the "intermediary" strategy).** The replacement does **not**
need to reverse the content protocol. It needs to (a) **emulate the modem/NAD
interface** the navi drives over USB CDC — the `+XNAD` / `DCM_Params` /
`NAVI_Info_sent` grammar (recovered) plus the USB enumeration (needs a capture);
(b) **route the navi's IP traffic** to the internet/server; (c) ensure the server
the navi targets is a live OpenCARWINGS that implements those endpoints
`[TO CONFIRM: where the navi points + OpenCARWINGS feature coverage]`; and (d)
**receive `navi info` and report it** for the EV features (grammar recovered). The
only remaining hard unknown is **physical** (USB descriptors, port, speed) — see
the routing/descriptor notes above.

## Navi presence is gated by the `AUDIO_TYPE` coding

The TCU only expects a navigation unit when its `AUDIO_TYPE` coding says so.
`AudioManagement` reads the `AUDIO_TYPE` value from NVM and decodes bits **[3:2]**
(`(val & 0xf) >> 2`) into one of four system types (`@0xA02F8CC4`)
`[VERIFIED: decomp @0xA02F8CC4]`:

| Decoded value | System type | Internal mode byte |
|---|---|---|
| 0 | `TYPE_NON_NAVI_SYSTEM` | 0 |
| 1 | audio system (no BTHF) | 3 |
| 2 | audio system (BTHF) | 1 |
| 3 | `TYPE_NAVI_SYSTEM_USB` (requires a BTHF flag set) | 2 |

Consequently the **`NAVI_ID` is only required when the unit is coded as
`TYPE_NAVI_SYSTEM_USB`**. The server-message content validators check identity in
a fixed order — VIN → DCM_ID → (NAVI_ID *only if navi-type*) → ICCID — and
otherwise log `No need to check NAVI ID because the current audio type is not
TYPE_NAVI_SYSTEM_USB` `[VERIFIED: decomp @0xA02BF9DC, @0xA02ED610, @0xA031A338]`.
Error codes returned by these validators: **`0x17` = no VIN, `0x05` = missing
DCM_ID / NAVI_ID / content error, `0x1B` = authentication failure**
`[VERIFIED: decomp]`.

What this means for emulation: to make the original AV unit + TCU pair behave as a
navi system, the coded `AUDIO_TYPE` must select navi, and the TCU must hold a
valid `NAVI_ID` (14 bytes, coding `0x27`). A replacement that wants to **omit**
the navi can leave `AUDIO_TYPE` non-navi and the `NAVI_ID` check is skipped
entirely `[VERIFIED: decomp]`.

## Emulation strategy (Phase 2)

The ESP32-S3 has a native USB OTG controller (host or device)
`[VERIFIED: ESP32-S3 datasheet, Espressif]`, which makes emulation plausible
regardless of the required role. But USB 1.0 low-speed in device mode has
specific constraints: `[TBD after the link speed is identified]`.

Validation plan:

1. Sniff the USB link between the original TCU and the AV unit (logic
   analyzer or USB capture board) `[TO MEASURE]`.
2. Replay the init exchanges from the ESP32-S3.
3. Identify the minimal command subset that keeps the AV unit satisfied.

## To verify

- [ ] Actual USB speed (low/full speed) `[TO MEASURE: logic analyzer]`
- [x] Host side of the link — firmware uses the USB device (function) stack, so
  TCU = device / AV unit = host `[TO CONFIRM: capture]`
- [x] Interface composition — **2× CDC + 1× Mass Storage**, a CDC composite
  device `[VERIFIED: product string descriptor]`
- [ ] Numeric descriptors (VID/PID, bcdUSB, endpoint map) `[TO MEASURE: USB
  capture]` — built in code, **not** a static blob `[VERIFIED: binary scan, 0
  hits]`; likely Comneon/Infineon defaults
- [ ] Active `+XSIO` variant on a live unit — decides which CDC port carries the
  AT/navi channel `[TO MEASURE: +XSIO? on a running TCU]`
- [x] `+XNAD_*` command inventory and `DCM_Params` grammar — recovered from the
  dump (see grammar table above) `[VERIFIED: decomp]`
- [x] What gates the `NAVI_ID` requirement — the `AUDIO_TYPE` coding (navi vs
  non-navi) `[VERIFIED: decomp @0xA02F8CC4]`
- [ ] AV unit behavior without a TCU `[TO MEASURE]`
