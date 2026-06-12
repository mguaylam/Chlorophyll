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

Proprietary AT commands of the **`+XNAD_*`** family exchanged over the CDC
link `[TO CONFIRM: firmware strings, nissan-leaf-tcu repo]`.

Command list, parameters and responses: `[TBD — inventory to build from the
firmware strings, without copying the firmware itself]`.

| Command | Assumed role | Status |
|---|---|---|
| `+XNAD_…` | `[TBD]` | `[TBD]` |

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
