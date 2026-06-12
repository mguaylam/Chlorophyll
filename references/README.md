# references/

External resources. **Nothing proprietary is mirrored here** — links only.
Do not commit firmware images, service manual PDFs, or captures to this
repository.

## Upstream projects

| Resource | Link | Notes |
|---|---|---|
| nissan-leaf-tcu | https://github.com/developerfromjokela/nissan-leaf-tcu | TCU reverse engineering, firmware analysis. Primary upstream reference. Proprietary binaries live there, not here. |
| OpenCARWINGS | https://github.com/developerfromjokela/opencarwings | Self-hosted CARWINGS-compatible server. Source of truth for the server protocol. Includes `test_server.py` (Phase 0 oracle). |

## Vehicle documentation

| Resource | Link / location | Notes |
|---|---|---|
| AZE0 service manual | `[TBD — owned copy; not redistributable]` | Source for M67/M68/M113 pinouts. Sections used: `[TBD: note section numbers here as they are used]` |
| MyNissanLeaf forum | https://mynissanleaf.com | CAN bus docs, TCU threads, 12V battery drain data. Cite specific threads in docs/ when used. |

## Security research

| Resource | Link | Notes |
|---|---|---|
| DEF CON 25 — Leaf telematics | `[TBD: exact talk title and link]` | Mickey Shkatov et al. |

## Hardware datasheets

| Resource | Link | Notes |
|---|---|---|
| ESP32-S3-WROOM-1 | https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf | MCU module |
| SIMCom A7670 | `[TBD: exact variant first — see docs/hardware.md]` | LTE Cat-1 modem |
| SN65HVD230 | https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf | CAN transceiver |

## Citation rule

Every fact imported into `docs/` must cite its source here (or inline) and
carry a status marker — see
[docs/reverse-engineering.md](../docs/reverse-engineering.md).
