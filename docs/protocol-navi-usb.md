# TCU ↔ navigation unit protocol (USB)

Internal link between the TCU and the AV (navigation) unit. **Phase 2**
(research) only.

> This entire document is unverified. Source: reverse engineering published in
> [nissan-leaf-tcu](https://github.com/developerfromjokela/nissan-leaf-tcu)
> `[TO CONFIRM: direct re-reading of the repo and of the firmware strings]`.

## Physical layer

- USB **1.0** (low/full speed: `[TBD]`) through the M68 connector
  `[TO CONFIRM: service manual]`. Pinout: [pinout.md](pinout.md).
- USB role on each side (who is host: the AV unit or the TCU?):
  `[TBD — determines whether the ESP32-S3 must act as device or host]`.
- USB class: CDC (virtual serial port) `[TO CONFIRM: nissan-leaf-tcu repo]`.

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
- [ ] Host side of the link `[TBD]`
- [ ] USB class / descriptors of the original TCU `[TO MEASURE: USB capture]`
- [ ] Inventory of `+XNAD_*` commands `[TBD]`
- [ ] AV unit behavior without a TCU `[TO MEASURE]`
