# 2G network status in Canada

> **Everything on this page is `[TO CONFIRM]`.** It records the working
> assumption that motivates the project; it must be backed by carrier
> announcements and, ideally, a field test (does the original TCU still
> register?).

## Working assumption

The original TCU is 2G (GSM/GPRS) only `[TO CONFIRM: nissan-leaf-tcu repo /
unit modem identification]`. In Canada:

- The major carriers (Bell, Telus, Rogers) have shut down or are shutting down
  their 2G networks `[TO CONFIRM: official carrier announcements — find dates
  and sources]`.
- Even where 2G coverage nominally remains, the Nissan-side service backend
  for CARWINGS in North America was discontinued `[TO CONFIRM: Nissan
  announcements / community reports]`.

Consequence: even a perfectly working original TCU has nothing to talk to —
hence the LTE + self-hosted OpenCARWINGS approach.

## Field check (to do)

- [ ] Does the original TCU register on any network today? (TCU diagnostic
  screen on the AV unit, or SIM/IMSI status) `[TO MEASURE]`
- [ ] Which carrier/MVNO did the original TCU use in Canada? `[TO CONFIRM]`
- [ ] Collect dated, linkable sources for the Bell/Telus/Rogers 2G shutdowns
  `[TO CONFIRM]`

## LTE alternative

Replacement plan: LTE Cat-1 modem + IoT SIM (or regular SIM) on a Canadian
carrier. Band compatibility: see [hardware.md](hardware.md). Monthly cost and
SIM provider: `[TBD]`.
