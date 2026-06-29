# Connectors and pinout

Primary source: **2015 Leaf NAM service manual** (AM-0ZE0-U0-0002-15,
revision June 2014), sections AV and PG — owned copy, not redistributed here.
Facts below cite the manual page. `[VERIFIED: SM AV-xxx]` means read directly
from the manual; a multimeter check before first wiring is still recommended
(harness variations, model-year drift).

Vehicle: Nissan Leaf AZE0, MY2015 (NAM). Original TCU: type GNOV1N,
SW 06.42R, HW 95048, Continental `[VERIFIED: owner's unit label]`.

## M67 — TCU main connector (white, 40-pin)

`[VERIFIED: SM AV-538 (signal table), AV-590 (voltage checks), PG-53
(connector list "M67 W/40: TCU")]`

| Terminal | Wire | Signal | Notes |
|---|---|---|---|
| 1 | W | B+ | Battery voltage at all times, 9–16 V |
| 2 | B | GND | Continuity to body ground |
| 3 | L | ACC | 12 V with power switch in ACC |
| 4 | W | IGN | 12 V with power switch ON |
| 9 | L | **EV CAN H** | Direct EV-CAN access at the TCU |
| 10 | G | **EV CAN L** | |
| 11 | — | listed "–" in SM, but see activation-request note below | `[VERIFIED: SM AV-538 — "–"]` / `[TO CONFIRM: OVMS]` |
| others | — | not connected / unlabeled | `[VERIFIED: SM AV-538 — listed as "–"]` |

**EV System Activation Request (candidate — TX path for remote climate)**:
OVMS reports that on the **2013–2016 Leaf (ZE0-0/1)** it generates the *"EV
System Activation Request Signal"* by feeding **+12 V to TCU connector pin 11**
— concretely, it wires its **DA26 pin 18 ("Ext 12V") to the TCU pin 11** with a
single conductor `[TO CONFIRM: OVMS Leaf docs — openvehicles, vehicle_nissanleaf]`.
This is the discrete line the factory TCU asserts to wake the EV system while the
car is off, so a replacement TCU likely must drive the same pin to do remote A/C
(see [evcan-telemetry.md](evcan-telemetry.md), Phase 1 TX).

> **Conflict to resolve — do not treat this as a verified mapping.** The NAM SM
> signal table lists **M67 terminal 11 as "–" (not connected)**
> `[VERIFIED: SM AV-538]`, which contradicts OVMS's "pin 11". Possible reasons:
> OVMS's "pin 11" is on a different connector or uses a different numbering
> (OVMS primarily documents EU/JDM cars); the NAM harness differs; or the signal
> exists but is unnamed on the SM pages read so far. `[TO MEASURE: with the
> factory TCU installed, probe the M67 "–" pins (esp. 11) for +12 V during an
> EV-system activation, and cross-check the SM wiring diagram for an "EV system
> activation / main-relay request" line]`.

Fuses `[VERIFIED: SM AV-590 (assignment), AV-529 (ratings in wiring
diagram)]`:

| Supply | Fuse # | Rating |
|---|---|---|
| BAT (term. 1) | 34 | 20 A |
| ACC or ON (term. 3) | 19 | 10 A |
| ON (term. 4) | 3 | 10 A |

**Design consequence**: power, ignition sensing and EV-CAN are all available
on this single connector — a replacement TCU can use M67 alone for Phase 1.

## M68 — TCU USB/voice connector to the AV unit (gray, 17-pin)

`[VERIFIED: SM AV-538 (TCU side), AV-540 (AV unit side), AV-587 (continuity
mapping)]`

USB link (TCU M68 ↔ AV unit M97 without Bose / M104 with Bose):

| TCU term. | Wire | Signal | AV term. | AV signal |
|---|---|---|---|---|
| 47 | BR | VBUS | 62 | USB VBUS |
| 48 | L | D− | 61 | USB D− |
| 55 | SHIELD | GND | 70 | USB GND |
| 56 | R | D+ | 69 | USB D+ |

Separate analog voice channel on the same connector
`[VERIFIED: SM AV-538/AV-540]`: TCU 41 (U VOICE) ↔ AV 68 (U-VOICE),
TCU 49 (D VOICE) ↔ AV 76 (D-VOICE), TCU 42 (VOICE GND) ↔ AV 67 (GND),
TCU 46 ↔ AV 63 ("MANUFACTURE SPECIFIC"), TCU 57 = connector chassis ground.

Who supplies VBUS (i.e. which side is USB host): `[TO MEASURE: voltage on
TCU 47 with TCU unplugged — if the AV unit drives 5 V, the AV unit is host]`.

Related DTC: U1A05 "USB COMM" = USB communication failure between TCU and AV
control unit `[VERIFIED: SM AV-587]`.

## M113 — TEL antenna feeder

`[VERIFIED: SM AV-588/AV-589]`

- Terminals **58/59**, coaxial feeder to the roof TEL antenna.
- Antenna-detection bias: terminal 58 reads **2.8 V** to ground with the
  feeder disconnected and power ON; a short raises DTC **U1A07**, an open
  feeder raises **U1A08** (TEL ANTENNA NO CONN). A replacement TCU that
  reuses this feeder should reproduce a plausible load, or those DTCs are
  the TCU's own business and disappear with it `[TBD: whether anything else
  monitors the antenna]`.
- Connector type Hirose GT16: `[TO CONFIRM — not stated in the SM pages read;
  came from upstream/forums]`.
- Antenna usable for LTE bands: `[TO MEASURE — see hardware.md]`.

## Related TCU DTCs (for reference)

`[VERIFIED: SM AV-585..589]`: U1A03 SIM card unreadable, U1A04 VIN not
written (VIN is written via CONSULT after TCU replacement — relevant when
swapping units), U1A05 USB comm, U1A07 TEL antenna short, U1A08 TEL antenna
not connected.

## Still to verify

- [ ] Multimeter sanity check of M67 1/2/3/4 before first wiring `[TO MEASURE]`
- [ ] VBUS direction on M68 (USB host side) `[TO MEASURE]`
- [ ] M113 connector type (Hirose GT16?) `[TO CONFIRM]`
- [ ] EV-CAN bitrate and frame IDs visible at M67 9/10 `[TO MEASURE: CAN
  sniffer on the TCU connector]`
- [ ] Which M67 pin (OVMS says 11) carries the "EV System Activation Request"
  +12 V discrete, vs the SM "–" listing `[TO CONFIRM / TO MEASURE]`
