# Hardware

> **Status: proposal, not final.** This BOM is a starting point for
> discussion; nothing has been bought, assembled, or validated.

## Proposed reference design

| Function | Part | Rationale | Status |
|---|---|---|---|
| MCU | ESP32-S3-WROOM-1 N16R8 | Native USB OTG (Phase 2), native TWAI/CAN controller, deep sleep, 16MB flash / 8MB PSRAM | Proposal |
| LTE modem (reference) | SIM7600G-H (LTE Cat-4, global) | Ubiquitous, ~$25-35, excellent AT/USB-CDC/PPP support, ~20 global LTE bands incl. the Canadian set (B4/B7/B12/B13/B66) — best "works + easy to document for international users" | Recommended reference `[VERIFIED: SIMCom band list]` |
| LTE modem (low-power alt.) | SIMCom A7670 (LTE Cat-1) | Lower power than Cat-4 (better for the <5 mA goal); pick the band variant per region | Optimization **after** it works; band variant `[TO CONFIRM]` |
| CAN transceiver | SN65HVD230 | 3.3V, standard with ESP32 | Proposal |
| Power supply | `[TBD]` | 12V automotive → 3.3V/4V; must survive automotive transients (load dump) | `[TBD: automotive-rated buck, TVS]` |

### Modem choice: international design, regional part

Chlorophyll is meant to be **international**, so the design treats the modem as a
**swappable module behind a standard AT + PPP/data interface** (UART or USB-CDC);
nothing in the protocol or firmware logic is modem-specific. Each builder then
picks a part whose LTE bands match their region. The reference build uses the
**SIM7600G-H** (global Cat-4) because it covers most of the world and is the most
documented, so the project's "getting started" path is reproducible everywhere.

**Why LTE, not 5G or 2G/3G:**

- The original TCU was **2G-only**, and 2G/3G are shutting down (Telus 3G off
  since **March 2025**; Rogers/Bell phased to **2027**) `[VERIFIED: carrier
  announcements — see sources]`. So LTE is mandatory now.
- **5G is the wrong tool**: modules cost ~$80-200 (vs ~$25-35 for SIM7600), draw
  far more power, and a CARWINGS packet is only a few hundred bytes — no bandwidth
  benefit. 5G networks keep an LTE fallback, so an LTE modem stays connected under
  5G coverage anyway. Carriers will keep LTE for IoT long after 3G.
- **LTE Cat-1 / Cat-1 bis** is the natural fit for telematics (low data, lower
  power than Cat-4); Cat-4 (SIM7600) is chosen only for support/availability.

### Regional LTE band reference

The modem must cover the operator's LTE bands. Canada (the maintainer's unit):

| Carrier(s) | Core LTE bands | Notes |
|---|---|---|
| Rogers / Bell / Telus | **B4, B7, B12, B13, B66, B71** (+ historical B2, B5, B17, B25) | They share much infrastructure `[VERIFIED: frequencycheck / carrier lists]` |

Module fit for Canada `[VERIFIED: SIMCom band lists]`:

- **SIM7600G-H (global)** — B1/2/3/4/5/7/8/12/13/18/19/20/25/26/28/66 + TDD
  34/38/39/40/41. Covers B4/B7/B12/B13/B66 → **fine for urban/suburban Canada**,
  but **no B71** (600 MHz) → weaker in some rural areas.
- **SIM7600NA-H (North America)** — adds **B71** and B14; better for rural Canada
  / the US.

Builders elsewhere: substitute the regional variant (e.g. SIM7600E-H for Europe).
The maintainer's call on G-H vs NA-H is a coverage trade-off, not a blocker.

### Open questions on the modem

- For **rural Canada**, decide SIM7600G-H vs SIM7600NA-H (B71) `[decision —
  coverage-dependent]`.
- Modem standby/PSM consumption — dominates the power budget `[TO CONFIRM:
  datasheet, then [TO MEASURE]]`. Cat-1 (A7670) is the lever if Cat-4 standby is
  too high.
- Confirm Bell/Telus/Rogers **provision Cat-1/Cat-1 bis** data SIMs (they do for
  IoT, but verify the chosen plan) `[TO CONFIRM: carrier IoT plan]`.
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

- [x] Canadian LTE bands + reference modem chosen (SIM7600G-H global; NA-H for
  rural B71) `[VERIFIED: carrier band lists + SIMCom]`
- [ ] G-H vs NA-H final call (rural coverage) `[decision]`
- [ ] Bell/Telus/Rogers IoT data plan provisions Cat-1/inbound-SMS `[TO CONFIRM]`
- [ ] Real standby consumption of the chosen modem `[TO MEASURE]`
- [ ] 12V battery spec and acceptable drain `[TO CONFIRM]`
- [ ] Automotive-grade power supply design `[TBD]`
- [ ] Original antenna usability in LTE `[TO MEASURE]`
