# Hardware

> **Status: proposal, not final.** This BOM is a starting point for
> discussion; nothing has been bought, assembled, or validated.

## Proposed reference design

| Function | Part | Rationale | Status |
|---|---|---|---|
| MCU | ESP32-S3-WROOM-1 N16R8 | Native USB OTG (Phase 2), native TWAI/CAN controller, deep sleep, 16MB flash / 8MB PSRAM | Proposal |
| LTE modem (reference) | **SIMCom A7670G** (LTE Cat-1, global) | Cheaper + lower power than Cat-4 (helps the <5 mA goal); **same LTE-FDD bands as SIM7600G-H** incl. the Canadian set (B4/B7/B12/B13/B66); 10/5 Mbps is ample for telemetry | **FIXED for the first prototype** `[VERIFIED: SIMCom band list]`. Must be the **`-G` (global)** variant — `-E` (Europe) lacks NA bands |
| LTE modem (alt.) | SIM7600G-H (LTE Cat-4, global) | Best community/AT documentation, integrated GNSS; higher cost/power | Fallback if A7670G support/GNSS is needed |
| CAN transceiver | SN65HVD230 | 3.3V, standard with ESP32 | Proposal |
| Power supply | `[TBD]` | 12V automotive → 3.3V/4V; must survive automotive transients (load dump) | `[TBD: automotive-rated buck, TVS]` |

### Modem choice: international design, regional part

Chlorophyll is meant to be **international**, so the design treats the modem as a
**swappable module behind a standard AT + PPP/data interface** (UART or USB-CDC);
nothing in the protocol or firmware logic is modem-specific. Each builder then
picks a part whose LTE bands match their region. The reference build uses the
**A7670G** (global Cat-1): it carries the same global LTE-FDD bands as the
SIM7600G-H but is cheaper and lower-power, which suits telematics and the standby
budget. The SIM7600G-H (Cat-4, integrated GNSS, best documentation) is the
fallback if more support or on-module GPS is wanted.

**Why LTE, not 5G or 2G/3G:**

- The original TCU was **2G-only**, and 2G/3G are shutting down (Telus 3G off
  since **March 2025**; Rogers/Bell phased to **2027**) `[VERIFIED: carrier
  announcements — see sources]`. So LTE is mandatory now.
- **5G is the wrong tool**: modules cost ~$80-200 (vs ~$25-35 for SIM7600), draw
  far more power, and a CARWINGS packet is only a few hundred bytes — no bandwidth
  benefit. 5G networks keep an LTE fallback, so an LTE modem stays connected under
  5G coverage anyway. Carriers will keep LTE for IoT long after 3G.
- **LTE Cat-1** is the natural fit for telematics (low data, lower power than
  Cat-4) — hence the A7670G reference; Cat-4 (SIM7600) is the fallback only for
  extra support/GNSS.

### Regional LTE band reference

The modem must cover the operator's LTE bands. Canada (the maintainer's unit):

| Carrier(s) | Core LTE bands | Notes |
|---|---|---|
| Rogers / Bell / Telus | **B4, B7, B12, B13, B66, B71** (+ historical B2, B5, B17, B25) | They share much infrastructure `[VERIFIED: frequencycheck / carrier lists]` |

Module fit for Canada `[VERIFIED: SIMCom band lists]`:

- **A7670G (global Cat-1)** — same LTE-FDD bands as SIM7600G-H
  (B1/2/3/4/5/7/8/12/13/18/19/20/25/26/28/66). Covers B4/B7/B12/B13/B66 →
  **fine for urban/suburban Canada**, but **no B71** (600 MHz) → weaker in some
  rural areas. Use the **`-G`** variant — `-E`/`-SA` are Europe/LATAM band sets.
- **SIM7600G-H (global Cat-4)** — same bands as above + TDD 34/38/39/40/41, plus
  integrated GNSS; the fallback if more documentation/GPS is wanted. No B71 either.
- **SIM7600NA-H (North America)** — adds **B71** and B14 if rural-Canada / US
  coverage matters.

Builders elsewhere: substitute the regional variant (e.g. A7670E for Europe).
B71 (rural) is the only Canadian gap in the reference part — a coverage
trade-off, not a blocker.

### Open questions on the modem

- For **rural Canada**, B71 is missing from the A7670G/SIM7600G-H; SIM7600NA-H
  covers it `[decision — coverage-dependent]`.
- Modem standby/PSM consumption — dominates the power budget `[TO CONFIRM:
  datasheet, then [TO MEASURE]]`. As a Cat-1 part the A7670G already draws less
  than Cat-4; for reference the SIM7600G-H in **sleep mode (`AT+CSCLK`) measures
  ~1-5 mA while still reachable via DRX paging** (community LilyGO-board figures,
  board overhead included), so even Cat-4 is in range — Cat-1 should be better
  `[TO CONFIRM: SIMCom datasheet; TO MEASURE on the real build]`. With the ESP32-S3
  in deep sleep (~tens of µA), the **<5 mA standby target is plausible**. PSM
  reaches ~µA but deregisters (wake latency). The swappable modem design means
  switching parts costs no protocol/firmware rework.
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

- [x] Canadian LTE bands + reference modem chosen (**A7670G** global Cat-1;
  SIM7600G-H fallback; NA-H for rural B71) `[VERIFIED: carrier band lists + SIMCom]`
- [ ] Rural-Canada B71 call (A7670G/G-H lack it; NA-H has it) `[decision]`
- [ ] Bell/Telus/Rogers IoT data plan provisions Cat-1/inbound-SMS `[TO CONFIRM]`
- [ ] Real standby consumption of the chosen modem `[TO MEASURE]`
- [ ] 12V battery spec and acceptable drain `[TO CONFIRM]`
- [ ] Automotive-grade power supply design `[TBD]`
- [ ] Original antenna usability in LTE `[TO MEASURE]`
