# TCU ↔ navigation unit protocol (USB)

Internal link between the TCU and the AV (navigation) unit. **Phase 2**
(research) only.

> This entire document is unverified. Source: reverse engineering published in
> [nissan-leaf-tcu](https://github.com/developerfromjokela/nissan-leaf-tcu)
> `[TO CONFIRM: direct re-reading of the repo and of the firmware strings]`.

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
- [ ] USB descriptors (VID/PID, the two CDC ports' roles) `[TO MEASURE: USB
  capture]` — class is CDC `[VERIFIED: firmware]`
- [ ] Inventory of `+XNAD_*` commands `[TBD]`
- [ ] AV unit behavior without a TCU `[TO MEASURE]`
