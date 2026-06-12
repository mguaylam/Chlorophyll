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
| 2015 Leaf NAM service manual | AM-0ZE0-U0-0002-15, rev. June 2014 — owned copy, not redistributable | Sections used so far: AV (TELEMATICS SYSTEM: wiring diagram AV-529+, connector tables AV-538/540, DTC/circuit diagnosis AV-585..591), PG (harness connector list PG-53) |
| MyNissanLeaf forum | https://mynissanleaf.com | CAN bus docs, TCU threads, 12V battery drain data. Cite specific threads in docs/ when used. |

## Original TCU hardware

| Resource | Link | Notes |
|---|---|---|
| FCC filing LHJGNOV1N | https://fcc.report/FCC-ID/LHJGNOV1N | 2G TCU (GNOV1N), Continental NOVANTO platform. Upstream notes: Freescale MC9S12XEQ512 (CAN) + Infineon PMB8876 (baseband/app), Nucleus RTOS `[TO CONFIRM: nissan-leaf-tcu device/README.md]` |
| TCU teardown thread | https://mynissanleaf.com/threads/tcu-teardown.34309/ | UART pinout (majbthrd) |

## Security research

| Resource | Link | Notes |
|---|---|---|
| DEF CON 25 — "Driving down the rabbit hole" | https://www.youtube.com/watch?v=5QBOmr_ZyLo | Mickey Shkatov, Jesse Michael, Oleksandr Bazhaniuk |

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
