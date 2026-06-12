# Chlorophyll — Open-source TCU for the Nissan Leaf AZE0 (2015)

**Status: very early / WIP — nothing works yet. Documentation under verification.**

Replacement TCU (Telematics Control Unit) for the Nissan Leaf AZE0, based on an
ESP32-S3 + LTE modem. The original TCU (type GNOV1N, Continental) is 2G-only;
the 2G network is dead or dying in Canada `[TO CONFIRM: see docs/network-2g-status.md]`,
which makes the telematics services (CARWINGS / NissanConnect EV) unusable.

Goal: a home-built TCU that speaks the CARWINGS protocol to a self-hosted
[OpenCARWINGS](https://github.com/developerfromjokela/opencarwings) server over
a modern IP stack (LTE), while remaining compatible with the original
navigation unit.

## Target architecture

```
                 ┌──────────────────────── Vehicle ─────────────────────────┐
                 │                                                          │
 ┌────────────┐  │  USB 1.0 (M68)   ┌──────────────────────┐   EV-CAN       │
 │  AV unit   │◄─┼─────────────────►│      Chlorophyll      │◄──────────────┼──► VCM / HVBAT / OBC
 │ (navi)     │  │  AT +XNAD_*      │  ESP32-S3 + LTE modem │   (TWAI)      │
 └────────────┘  │                  └──────────┬───────────┘                │
                 │       12V (M67) ────────────┤                            │
                 └──────────────────────────── │ ──────────────────────────-┘
                                               │ LTE (TCP :55230)
                                               ▼
                                  ┌─────────────────────────┐
                                  │   OpenCARWINGS server   │
                                  │      (self-hosted)      │
                                  └─────────────────────────┘
```

Details: [docs/architecture.md](docs/architecture.md)

## Roadmap

- **Phase 0** — Python client for the server protocol, tested against
  OpenCARWINGS' `test_server.py`. Zero hardware: validate the protocol
  understanding (port 55230, packets, auth) before touching a soldering iron.
- **Phase 1** — ESP32-S3 + LTE hardware: remote A/C, charge control,
  telemetry (SOC, range) over EV-CAN. The bare minimum to get the app
  features back.
- **Phase 2 (research)** — Navi screen services by emulating the original USB
  link (AT `+XNAD_*` commands). Feasibility not demonstrated.

## Documentation

| Document | Contents |
|---|---|
| [architecture.md](docs/architecture.md) | System overview |
| [protocol-server.md](docs/protocol-server.md) | TCU ↔ server protocol (port 55230) |
| [protocol-navi-usb.md](docs/protocol-navi-usb.md) | TCU ↔ AV unit USB link (AT +XNAD) |
| [pinout.md](docs/pinout.md) | M67 / M68 / M113 connectors |
| [hardware.md](docs/hardware.md) | Proposed BOM, power budget |
| [reverse-engineering.md](docs/reverse-engineering.md) | Methodology and credits |
| [network-2g-status.md](docs/network-2g-status.md) | 2G status in Canada |

**Epistemic stance**: every technical claim in this documentation carries a
status marker — `[VERIFIED: source]`, `[TO CONFIRM: source]`, `[TO MEASURE]`
or `[TBD]`. Anything without a `VERIFIED` marker must not be taken for
granted. Do not wire anything based on a `[TO CONFIRM]`.

## Legal notice

- This project **does not redistribute any proprietary firmware** from
  Nissan/Continental. Analyses rely on work published in third-party
  repositories, referenced in [references/](references/README.md), never
  copied here.
- All code in this repository is original.
- **Use at your own risk.** Working on a vehicle's wiring and CAN bus can
  damage the vehicle or create a safety hazard. No warranty.
- Sustainability / right-to-repair project, **not affiliated with Nissan**,
  Continental, or any manufacturer. Trademarks belong to their owners.

## Credits

- [developerfromjokela](https://github.com/developerfromjokela) — TCU reverse
  engineering ([nissan-leaf-tcu](https://github.com/developerfromjokela/nissan-leaf-tcu))
  and the [OpenCARWINGS](https://github.com/developerfromjokela/opencarwings) server.
- Mickey Shkatov and the DEF CON 25 team — foundational work on Leaf
  telematics security.
- The [MyNissanLeaf](https://mynissanleaf.com) community — years of collective
  documentation.

## License

[GPLv3](LICENSE). Deliberate choice: this project exists to extend the life of
vehicles whose manufacturer abandoned their services. Copyleft guarantees that
any improvement or derivative (commercial included) stays open and benefits
Leaf owners, rather than being closed off. If you want to embed this code in a
closed product, this is not the right repository.
