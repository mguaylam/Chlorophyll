# EV-CAN telemetry

What the replacement TCU must **read** from the vehicle bus to fill the
CARWINGS DATA (type 3) packet, and the candidate CAN frames to get it from.

> **Provenance warning.** The upstream repos document the *server protocol
> body*, not the raw EV-CAN frames the original TCU reads from the car. The
> frame IDs and byte layouts below are harvested from community knowledge
> (MyNissanLeaf CAN wiki, LeafSpy, open Leaf CAN-decoder projects). **None of
> it is verified against this vehicle.** Treat this page as a checklist to
> confirm with a CAN sniffer, not as settled fact. Every ID is
> `[TO CONFIRM: community]` and every extraction is `[TO MEASURE: sniff]`.

## Bus access and parameters

- Tap point: **M67 terminals 9 (EV CAN H) / 10 (EV CAN L)** at the TCU
  connector `[VERIFIED: 2015 Leaf NAM SM, AV-538]`.
- Bitrate: the Leaf EV-CAN is **500 kbit/s** `[TO CONFIRM: community —
  verify by sniffing; the ESP32-S3 TWAI controller must be set to match]`.
- The replacement should be **listen-only first** (TWAI in listen-only mode)
  to characterize traffic before transmitting anything
  (see [architecture.md](architecture.md)).

## Signals we need (target = GDC EV-info body)

These are the fields the type-3 body carries (see
[protocol-server.md](protocol-server.md) and `tools/carwings`); each must be
sourced from one or more CAN frames.

| GDC field | Meaning | Likely source |
|---|---|---|
| `soc` | State of charge % | battery controller (LBC/HVBAT) |
| `gids` | Usable energy in "gids" (~80 Wh each per GDC) | LBC |
| `soh` | State of health % | LBC |
| `pluggedin` | Charging cable connected | OBC / VCM |
| `charging` / `quick_charging` | AC / DC charging active | OBC / VCM |
| `acstate` | Climate (A/C) running | HVAC / VCM |
| `range_acon` / `range_acoff` | Estimated range | VCM (or computed) |
| `ignition`, `parked`, `direction_forward` | Power state, gear | VCM |

## Candidate frames to verify

**Do not trust offsets/scaling here — confirm each against a cross-checked
community source AND a real capture before use.**

| CAN ID | Module | Carries (claimed) | Status |
|---|---|---|---|
| 0x1DB | LBC (HVBAT) | Pack current & voltage, some SOC/limit flags | `[TO CONFIRM: community]` `[TO MEASURE]` |
| 0x1DC | LBC | Charge/discharge power limits | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x55B | LBC | SOC (display), ~0.1% resolution | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x5BC | LBC | GIDs (remaining energy), muxed capacity/SOH bars | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x5B3 | LBC | SOH, SOC, temperature (muxed) | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x5C0 | LBC | Battery temperature (muxed) | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x11A | VCM | Shift/gear, power/ignition state | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x1F2 | VCM/OBC | Charge command, plug state | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x390 / 0x393 | OBC | On-board charger status (AC/DC, active) | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x60D | VCM/BCM | Plug lock, doors, some A/C/charge flags | `[TO CONFIRM]` `[TO MEASURE]` |
| 0x54B / 0x54C | HVAC | Climate / heater state | `[TO CONFIRM]` `[TO MEASURE]` |

Frame IDs differ between ZE0 (2011–12) and AZE0 (2013–15) and across battery
sizes — this project targets the **AZE0 24 kWh** specifically `[TO CONFIRM]`.

## How to verify (the actual next step)

1. **Sniff, listen-only.** ESP32-S3 TWAI (or a USB-CAN + `candump`) on M67
   9/10. Confirm 500 kbit/s by getting a clean, error-free capture.
2. **Correlate.** Log while changing one variable at a time — plug in, start
   charging, turn on climate, shift gears — and watch which bytes move. This
   is how offsets/scaling get pinned down, independent of community claims.
3. **Cross-check** each confirmed signal against a second community source
   before promoting it to `[VERIFIED: capture <date>]`.
4. Raw captures stay out of the repo (`.gitignore` excludes `*.pcap`,
   `dumps/`) — they can contain VIN/identifiers.

## Reference sources to harvest from

- MyNissanLeaf "CAN bus" wiki/threads (see [references/](../references/README.md)).
- Open Leaf CAN-decoder projects and LeafSpy field documentation.
- `nissan-leaf-tcu/communication/body_documentation/` for the *target* body
  format (what the values must become), not the raw CAN.

## Commands (Phase 1, transmit — later)

Reading is passive and safe. **Sending** frames to trigger remote A/C or
charge is a separate, higher-risk task: `[TBD — do not attempt until reading
is solid and the vehicle is parked; the original TCU's TX behavior must be
characterized first]`. See the charge/AC command codes the server expects in
[protocol-server.md](protocol-server.md).
