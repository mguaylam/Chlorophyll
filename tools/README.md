# tools/

Host-side tooling. **Placeholder — no code yet.**

## Planned: Python protocol client (Phase 0)

A minimal Python implementation of the TCU side of the CARWINGS protocol,
tested against `scripts/test_server.py` (nissan-leaf-tcu repo) and a local
OpenCARWINGS `tcuserver`. Goals:

1. Validate (or correct) every claim in
   [docs/protocol-server.md](../docs/protocol-server.md): framing, packet
   types 1/3/5, password hash (standard CRC-32 over password +
   `"evtelematics"` — `[VERIFIED: opencarwings@3927dad]`).
2. Serve as the executable reference for the C implementation in `firmware/`.
3. Provide a fake-TCU for testing a self-hosted OpenCARWINGS server without a
   vehicle.

## Possible later additions

- EV-CAN log decoder (candump → telemetry).
- USB capture analyzer for the `+XNAD_*` link (Phase 2).

Code and comments in English. Python ≥ 3.11, no heavy dependencies.
