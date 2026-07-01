"""Conformance test against the *actual* upstream server code.

The other test module (test_protocol.py) round-trips our packets through
decoders we re-implemented from the spec. Those catch our own regressions but
not drift from upstream, because both sides live in this repo. This module
imports the real reference implementations and runs our packets through them,
so it fails the day upstream's byte layout stops matching ours.

It is opt-in: set the env vars to local clones and run pytest. Without them the
whole module is skipped, so the default `pytest` run stays hermetic.

    CHLOROPHYLL_OPENCARWINGS_DIR=/path/to/opencarwings \
    CHLOROPHYLL_NISSAN_LEAF_TCU_DIR=/path/to/nissan-leaf-tcu \
        pytest tests/test_upstream_conformance.py -v

Clone the references (pinned to the commits our protocol was written against):
    git clone https://github.com/developerfromjokela/opencarwings      # 3927dad
    git clone https://github.com/developerfromjokela/nissan-leaf-tcu   # test_server
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from carwings.crc import password_hash as our_password_hash
from carwings.protocol import (
    BodyType,
    EvInfo,
    GpsFix,
    TcuIdentity,
    build_data_packet,
    build_init_packet,
    parse_response,
)

OPENCARWINGS_DIR = os.environ.get("CHLOROPHYLL_OPENCARWINGS_DIR")

pytestmark = pytest.mark.skipif(
    not OPENCARWINGS_DIR,
    reason="set CHLOROPHYLL_OPENCARWINGS_DIR to a local opencarwings clone",
)


def _load_upstream():
    """Import the upstream gdc_proto modules without pulling in Django.

    parser.py does `from tculink.gdc_proto.datafields import ...`, so the clone
    root (the directory that contains `tculink/`) must be on sys.path. Both
    `tculink/__init__.py` and `gdc_proto/__init__.py` are Django-free, so this
    imports cleanly.
    """
    root = Path(OPENCARWINGS_DIR).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import tculink.gdc_proto.parser as parser  # noqa: E402
    from tculink.utils import password_hash as pw  # noqa: E402
    from tculink.gdc_proto import responses  # noqa: E402

    return parser, pw, responses


IDENTITY = TcuIdentity(
    vin="1N4AZ0CPXFC300000",
    tcu_model="GNOV1N",
    unit_id="259C100000",
    iccid="8912230000000000000",
    username="owner",
    password="LEAF2015!",
)


def test_password_hash_matches_upstream():
    _, pw, _ = _load_upstream()
    for secret in ("", "test", "password", "LEAF2015!", "a-b_c=d+e@f#g?h!"):
        assert our_password_hash(secret) == pw.password_hash(secret), secret


def test_init_packet_parses_upstream():
    parser, _, _ = _load_upstream()
    gps = GpsFix(45.5017, -73.5673)  # Montréal
    pkt = build_init_packet(IDENTITY, gps)

    parsed = parser.parse_gdc_packet(pkt)

    assert parsed["message_type"] == (1, "INIT")
    assert parsed["body_type"] == "logon"

    tcu = parsed["tcu"]
    assert tcu["vin"] == IDENTITY.vin
    assert tcu["tcu_id"] == IDENTITY.tcu_model
    assert tcu["unit_id"] == IDENTITY.unit_id
    assert tcu["iccid"] == IDENTITY.iccid
    assert tcu["sw_version"] == IDENTITY.sw_version
    assert tcu["vehicle_descriptor"] == 0x92  # AZE0

    auth = parsed["auth"]
    assert auth["user"] == IDENTITY.username
    assert auth["pass"] == our_password_hash(IDENTITY.password)

    g = parsed["gps"]
    assert g["valid_position"] is True
    assert g["latitude"] == pytest.approx(45.5017, abs=1e-3)
    assert g["longitude"] == pytest.approx(-73.5673, abs=1e-3)


def test_data_packet_telemetry_parses_upstream():
    parser, _, _ = _load_upstream()
    ev = EvInfo(
        soc=82.5,
        gids=240,
        soh=92,
        plugged_in=True,
        charging=True,
        ac_on=False,
        ignition=True,
        range_acon=110,
        range_acoff=130,
    )
    pkt = build_data_packet(IDENTITY, BodyType.CHARGE_STATUS, ev, GpsFix(45.5, -73.5))

    parsed = parser.parse_gdc_packet(pkt)
    assert parsed["message_type"] == (3, "DATA")
    assert parsed["body_type"] == "charge_status"

    body = parsed["body"]
    assert body["soc"] == pytest.approx(82.5, abs=0.05)
    assert body["gids"] == 240
    assert body["soh"] == 92
    assert body["pluggedin"] is True
    assert body["charging"] is True
    assert body["quick_charging"] is False
    assert body["acstate"] is False
    assert body["ignition"] is True
    assert body["acon"] == 110
    assert body["acoff"] == 130


@pytest.mark.parametrize(
    "builder, dest, cmd",
    [
        ("create_charge_status_response", 0x28, 1),
        ("create_charge_request_response", 0x2B, 2),
        ("create_ac_setting_response", 0x2C, 3),
        ("create_ac_stop_response", 0x2C, 4),
    ],
)
def test_response_parsing_matches_upstream(builder, dest, cmd):
    """Our parse_response decodes the bytes upstream's builders emit.

    Note the upstream helpers invert `success`: create_charge_status_response(
    success=True) forwards `not success` as the success flag, so a "success"
    call actually sets the failure bit. We assert on the raw bytes it produces,
    not on that quirk.
    """
    _, _, responses = _load_upstream()
    raw = getattr(responses, builder)(success=True)
    resp = parse_response(raw)
    assert resp.destination == dest
    assert resp.command == cmd


def test_test_server_prefix_gap_is_real():
    """Document the nissan-leaf-tcu test_server.py AZE0 gap in an executable form.

    test_server.py matches logon with `data.startswith(b'\\x01\\x02\\x00')`,
    i.e. it hardcodes byte[1]==0x02 (a ZE0 descriptor). Our AZE0 packets carry
    0x92 there, which is what the opencarwings parser expects. So our packets
    are correct for the real server but are silently ignored by that specific
    test harness. This test pins the discrepancy so it is not mistaken for a
    bug in our builder.
    """
    tcu_dir = os.environ.get("CHLOROPHYLL_NISSAN_LEAF_TCU_DIR")
    if not tcu_dir:
        pytest.skip("set CHLOROPHYLL_NISSAN_LEAF_TCU_DIR to check test_server.py")
    src = (Path(tcu_dir) / "scripts" / "test_server.py").read_text()
    assert "01 02 00" in src  # the hardcoded ZE0 prefix
    aze0_pkt = build_init_packet(IDENTITY)
    assert aze0_pkt[1] == 0x92
    assert not aze0_pkt.startswith(bytes.fromhex("01 02 00"))
