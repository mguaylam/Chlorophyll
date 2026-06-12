# Connectors and pinout

> **Warning: nothing on this page is verified against the actual vehicle.**
> Every value must be cross-checked in the AZE0 service manual and measured
> with a multimeter before wiring anything. A wiring error on M67 can damage
> the TCU, the harness, or worse.

Vehicle: Nissan Leaf AZE0, model year 2015. Original TCU: type GNOV1N,
SW 06.42R, HW 95048, Continental `[VERIFIED: owner's unit label]`.

## M67 — power connector

`[TO CONFIRM: service manual — to be cross-checked, then [TO MEASURE:
multimeter, with connector unplugged then live]]`

| Pin | Signal | Notes |
|---|---|---|
| 1 | BAT +12V (permanent) | `[TO CONFIRM]` `[TO MEASURE]` |
| 2 | GND | `[TO CONFIRM]` `[TO MEASURE]` |
| 3 | ACC | `[TO CONFIRM]` `[TO MEASURE]` |
| 4 | ON (ignition) | `[TO CONFIRM]` `[TO MEASURE]` |

Associated fuses: **34 / 19 / 3** `[TO CONFIRM: service manual — identify
which fuse protects which line, and their ratings: [TBD]]`.

## M68 — USB connector to the AV unit

`[TO CONFIRM: service manual]`

Terminal mapping `[TO CONFIRM]`:

| TCU terminal | AV unit terminal | Signal |
|---|---|---|
| 47 | 62 | `[TBD]` |
| 48 | 61 | `[TBD]` |
| 55 | 70 | `[TBD]` |
| 56 | 69 | `[TBD]` |

Which pair carries D+/D−, which is VBUS/GND (if present), shielding: `[TBD —
service manual + multimeter]`.

## M113 — TEL antenna

- Connector: M113, terminals **58/59** `[TO CONFIRM: service manual]`.
- Connector type: Hirose **GT16** `[TO CONFIRM]`.
- Antenna usable for LTE (bands, VSWR): `[TBD — see hardware.md]`.

## To verify

- [ ] M67 pinout (4 pins) `[TO MEASURE: multimeter]`
- [ ] Role and rating of fuses 34/19/3 `[TO CONFIRM: service manual]`
- [ ] M68 47/48/55/56 ↔ 62/61/70/69 mapping and USB signal assignment `[TO CONFIRM]`
- [ ] Hirose GT16 connector on M113 `[TO CONFIRM]`
- [ ] Antenna behavior in LTE bands `[TO MEASURE: VNA/VSWR if possible]`
