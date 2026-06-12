"""Connect to a CARWINGS server as a fake TCU and run a logon + telemetry.

Usage:
    python examples/fake_tcu.py [host] [port]

Defaults to 127.0.0.1:55230. Point it at a running test_server.py
(nissan-leaf-tcu/scripts) or a local OpenCARWINGS tcuserver.
"""

import sys

from carwings.client import TcuClient
from carwings.protocol import (
    BodyType,
    EvInfo,
    GpsFix,
    TcuIdentity,
    VEHICLE_DESCRIPTOR_AZE0,
)

# Dummy identity — replace with your registered car's values when testing
# against a real OpenCARWINGS instance.
IDENTITY = TcuIdentity(
    vin="1N4AZ0CPXFC300000",
    tcu_model="GNOV1N",
    unit_id="259C100000",
    iccid="8912230000000000000",
    username="owner",
    password="LEAF2015!",
    vehicle_descriptor=VEHICLE_DESCRIPTOR_AZE0,
)


def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 55230

    client = TcuClient(host, port)
    with client.connect():
        print(f"Connected to {host}:{port}")

        resp = client.send_init(IDENTITY, GpsFix(45.5017, -73.5673))
        if resp is None:
            print("INIT: no response from server")
        else:
            print(f"INIT response: {resp.name} success={resp.success} "
                  f"raw={resp.raw.hex().upper()}")

        ev = EvInfo(soc=82.5, gids=240, plugged_in=True, charging=True)
        reply = client.send_data(IDENTITY, BodyType.CHARGE_STATUS, ev,
                                 GpsFix(45.5017, -73.5673))
        print(f"DATA reply: {reply.hex().upper() if reply else '(none)'}")


if __name__ == "__main__":
    main()
