# firmware/

Original ESP32-S3 firmware for the Chlorophyll TCU. **Placeholder — no code
yet** (Phase 1 starts after the protocol is validated in Phase 0).

This directory will never contain Nissan/Continental firmware. Only original
code, licensed under GPLv3 like the rest of the repository.

## Target structure

```
firmware/
├── platformio.ini          # or ESP-IDF CMake project — [TBD: PlatformIO vs pure ESP-IDF]
├── src/
│   ├── main.c
│   ├── carwings/           # server protocol client (port of the Phase 0 Python client)
│   ├── evcan/              # EV-CAN (TWAI) interface: decode telemetry, send commands
│   ├── modem/              # LTE modem driver (AT over UART), PPP or modem TCP stack
│   ├── power/              # sleep/wake state machine, power budget enforcement
│   └── navi_usb/           # Phase 2: AV unit USB link emulation (+XNAD)
└── test/                   # host-side unit tests (protocol framing, CRC)
```

## Design constraints (from docs/)

- Standby draw < 5 mA average — the sleep/wake state machine is a first-class
  feature, not an afterthought (see [docs/hardware.md](../docs/hardware.md)).
- Passive on the CAN bus by default (see [docs/architecture.md](../docs/architecture.md)).
- Protocol logic must be testable on the host without hardware (same framing
  code exercised by `tools/` and CI).

Code and comments in English.
