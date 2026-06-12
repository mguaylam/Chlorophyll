# Hardware

> **Status: proposal, not final.** This BOM is a starting point for
> discussion; nothing has been bought, assembled, or validated.

## Proposed reference design

| Function | Part | Rationale | Status |
|---|---|---|---|
| MCU | ESP32-S3-WROOM-1 N16R8 | Native USB OTG (Phase 2), native TWAI/CAN controller, deep sleep, 16MB flash / 8MB PSRAM | Proposal |
| LTE modem | SIMCom A7670 (LTE Cat-1) | Cheap, Cat-1 is plenty for telemetry | `[TO CONFIRM: band support for Bell/Telus/Rogers — see below]` |
| LTE modem (alt.) | SIM7600G-H | Global band coverage, better documented | Fallback if A7670 bands don't fit |
| CAN transceiver | SN65HVD230 | 3.3V, standard with ESP32 | Proposal |
| Power supply | `[TBD]` | 12V automotive → 3.3V/4V; must survive automotive transients (load dump) | `[TBD: automotive-rated buck, TVS]` |

### Open questions on the modem

- Exact A7670 variant (A7670E/SA/G…) and its LTE bands vs the bands used by
  Bell/Telus/Rogers `[TO CONFIRM: SIMCom datasheet + carrier band lists]`.
- Modem standby/PSM consumption — dominates the power budget `[TO CONFIRM:
  datasheet, then [TO MEASURE]]`.
- Remote wake-up is **SMS-based** in OpenCARWINGS (the server texts the SIM,
  the TCU then phones home) `[VERIFIED: opencarwings@3927dad — see
  protocol-server.md]`. Consequence: the modem must receive SMS while the
  system sleeps (modem registered, ESP32 in deep sleep, wake on modem RI/URC
  pin), **and the SIM plan must include inbound SMS** `[TO CONFIRM: plan]`.
  Registered-idle modem consumption is therefore the critical figure
  `[TO MEASURE]`.

## Power budget

Constraint: the AZE0 12V battery is small (group 51R, ~12V / 43Ah)
`[TO CONFIRM: spec of the actual installed battery]`. Community consensus on
healthy parasitic drain: **< 50 mA total vehicle** `[TO CONFIRM: MyNissanLeaf
forum]`.

**Target for this TCU: < 5 mA average in standby.**

Tracks to get there `[TBD — to validate by measurement]`, mirroring how the
original TCU does it (`[VERIFIED: firmware strings — see
firmware-findings.md]`: it keeps the baseband asleep and uses a small
always-on controller to wake it on ACC, a periodic timer, or modem activity):

- ESP32-S3 deep sleep (a few tens of µA) + periodic wake-up.
- Modem in PSM/eDRX if remote wake-up allows it, otherwise full modem
  power-off and acceptance of command latency.
- Wake on vehicle activity: ACC line (M67 pin 3), CAN activity, and modem RI
  on inbound SMS.

Every figure in this section is `[TO MEASURE: bench ammeter / µCurrent]` once
a prototype exists.

## Antenna

Reuse of the original TEL antenna (M113): `[TBD — original antenna designed
for 2G (850/1900 MHz?); LTE bands partially overlap. To characterize or
replace with a standalone LTE antenna]`.

## To verify

- [ ] A7670 variant and LTE bands vs Canadian carriers `[TO CONFIRM]`
- [ ] Real standby consumption of the chosen modem `[TO MEASURE]`
- [ ] 12V battery spec and acceptable drain `[TO CONFIRM]`
- [ ] Automotive-grade power supply design `[TBD]`
- [ ] Original antenna usability in LTE `[TO MEASURE]`
