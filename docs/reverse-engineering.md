# Reverse engineering — methodology and credits

This project writes **no proprietary firmware to disk in this repository** and
redistributes none. The analysis work below either references third-party
publications, or describes methodology applied locally by the project owner on
firmware extracted from their own unit.

## Prior work (credits)

- **[nissan-leaf-tcu](https://github.com/developerfromjokela/nissan-leaf-tcu)**
  (developerfromjokela) — firmware dumps, protocol notes, groundwork for
  [OpenCARWINGS](https://github.com/developerfromjokela/opencarwings). The
  primary upstream reference for this project.
- **Mickey Shkatov and the DEF CON 25 team** — Leaf telematics security
  research.
- **MyNissanLeaf community** — CAN bus documentation, TCU removal reports, 12V
  battery drain data.

See [references/](../references/README.md) for the full link list.

## Methodology

Each technique below feeds the docs with facts carrying explicit status
markers.

### 1. Strings and static analysis

- `strings` on the firmware images published upstream → inventory of AT
  commands (`+XNAD_*`), URLs, error messages.
- Ghidra for control flow around interesting strings (auth, packet framing).
- Output: facts marked `[TO CONFIRM: firmware strings]` until corroborated by
  a second source.

### 2. Server-side reading

- The OpenCARWINGS code is the cleanest source for the server protocol
  (port, packet types, password hash). Reading the code yields facts marked
  `[TO CONFIRM: opencarwings code]`, upgraded to `[VERIFIED: opencarwings
  code + test]` once exercised against `test_server.py` (Phase 0).

### 3. Live capture (when hardware is available)

- **EV-CAN sniffing** with the original TCU in place: which frames does it
  read, which (if any) does it send.
- **USB sniffing** of the TCU ↔ AV unit link (logic analyzer): init sequence,
  USB descriptors, `+XNAD_*` traffic.
- Output: facts marked `[VERIFIED: capture <date>]` with the capture method
  noted. Raw captures stay out of the repo (see .gitignore) since they may
  contain identifiers (VIN, IMEI, IMSI).

### 4. Bench measurements

- Multimeter on M67/M68 before any wiring.
- Current measurements for the power budget.
- Output: facts marked `[VERIFIED: measured <date>]`.

## Marker discipline

| Marker | Meaning |
|---|---|
| `[VERIFIED: source]` | Corroborated by a primary source or measured |
| `[TO CONFIRM: source]` | Claimed by the cited source, not yet corroborated |
| `[TO MEASURE]` / `[TO MEASURE: tool]` | Needs a physical measurement |
| `[TBD]` | Unknown — no reliable claim available yet |

Rule: a fact is promoted to `VERIFIED` only with the source or measurement
recorded next to it. Never silently delete a marker.
