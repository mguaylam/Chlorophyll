"""Round-trip the packets we build through decoders that mirror the server.

The decoders here reproduce the field slicing of opencarwings@3927dad
(parser/datafields) so the tests fail if our offsets drift from the server's.
They are intentionally independent re-implementations, not copied code.
"""

import struct

import pytest

from carwings.crc import password_hash
from carwings.protocol import (
    AUTH_OFFSET,
    BODY_OFFSET,
    BODY_TYPE_OFFSET,
    GPS_OFFSET,
    BodyType,
    EvInfo,
    GpsFix,
    PacketType,
    TcuIdentity,
    build_data_packet,
    build_init_packet,
    parse_response,
)

IDENTITY = TcuIdentity(
    vin="1N4AZ0CPXFC300000",
    tcu_model="GNOV1N",
    unit_id="259C100000",
    iccid="8912230000000000000",
    username="owner",
    password="LEAF2015!",
)


# --- decoders mirroring the server (offsets from opencarwings) --------------

def decode_tcu_info(packet):
    veh = packet[4:]
    return {
        "vehicle_descriptor": packet[1],
        "vin": veh[5:22].decode("ascii").rstrip("\x00").strip(),
        "tcu_id": veh[23:35].decode("ascii").rstrip("\x00").strip(),
        "unit_id": veh[52:64].decode("ascii").rstrip("\x00").strip(),
        "iccid": veh[65:85].decode("ascii").rstrip("\x00").strip(),
        "sw_version": veh[86:95].decode("ascii").rstrip("\x00").strip(),
    }


def decode_auth(packet):
    block = packet[AUTH_OFFSET:AUTH_OFFSET + 34]
    return {
        "user": block[1:16].decode("ascii").rstrip("\x00").strip(),
        "pass": block[18:33].decode("ascii").rstrip("\x00").strip(),
    }


def decode_gps(packet):
    b = packet[GPS_OFFSET:GPS_OFFSET + 16]
    home_byte = b[5]
    lat_mode = "N" if (home_byte >> 5) & 1 == 0 else "S"
    lon_mode = "E" if (home_byte >> 4) & 1 == 0 else "W"
    lat = b[6] + b[7] / 60.0 + (struct.unpack(">H", b[8:10])[0] / 100.0) / 3600.0
    lon = b[10] + b[11] / 60.0 + (struct.unpack(">H", b[12:14])[0] / 100.0) / 3600.0
    if lat_mode == "S":
        lat = -lat
    if lon_mode == "W":
        lon = -lon
    return {"valid": bool((home_byte >> 7) & 1), "lat": lat, "lon": lon}


def decode_evinfo(body):
    charge_state = (body[9] >> 6) & 0b11
    gids = (body[14] << 2) | ((body[15] & 0b11000000) >> 6)
    soc = (((body[16] & 0b01111111) << 4) | ((body[17] & 0b11110000) >> 4)) / 20
    return {
        "plugged_in": (body[9] & 1) == 1,
        "charging": charge_state == 1,
        "quick_charging": charge_state == 2,
        "ac_on": bool((body[9] >> 1) & 1),
        "ignition": bool((body[9] >> 5) & 1),
        "gids": gids,
        "soc": soc,
    }


# --- tests ------------------------------------------------------------------

def test_init_packet_shape_and_prefix():
    pkt = build_init_packet(IDENTITY)
    assert len(pkt) == 153
    assert pkt[0] == PacketType.INIT
    assert pkt[BODY_TYPE_OFFSET] == BodyType.LOGON
    # AZE0 descriptor; prefix is "01 92 00" for AZE0 (ZE0 would be "01 02 00").
    assert pkt[1] == 0x92
    assert pkt[2] == 0x00


def test_init_identity_round_trip():
    pkt = build_init_packet(IDENTITY)
    info = decode_tcu_info(pkt)
    assert info["vin"] == IDENTITY.vin
    assert info["tcu_id"] == IDENTITY.tcu_model
    assert info["unit_id"] == IDENTITY.unit_id
    assert info["iccid"] == IDENTITY.iccid
    assert info["sw_version"] == IDENTITY.sw_version


def test_init_auth_hash_round_trip():
    pkt = build_init_packet(IDENTITY)
    auth = decode_auth(pkt)
    assert auth["user"] == IDENTITY.username
    assert auth["pass"] == password_hash(IDENTITY.password)


def test_gps_round_trip():
    pkt = build_init_packet(IDENTITY, GpsFix(45.5017, -73.5673))  # Montréal
    gps = decode_gps(pkt)
    assert gps["valid"] is True
    assert gps["lat"] == pytest.approx(45.5017, abs=1e-3)
    assert gps["lon"] == pytest.approx(-73.5673, abs=1e-3)


def test_data_packet_telemetry_round_trip():
    ev = EvInfo(soc=82.5, gids=240, plugged_in=True, charging=True, ac_on=False)
    pkt = build_data_packet(IDENTITY, BodyType.CHARGE_STATUS, ev)
    assert pkt[0] == PacketType.DATA
    body = pkt[BODY_OFFSET:]
    decoded = decode_evinfo(body)
    assert decoded["soc"] == pytest.approx(82.5, abs=0.05)
    assert decoded["gids"] == 240
    assert decoded["plugged_in"] is True
    assert decoded["charging"] is True
    assert decoded["ac_on"] is False


def test_parse_charge_status_response():
    # 02 00 0008 28 02 00 90 — destination 0x28, command 1, failure bit set
    resp = parse_response(bytes.fromhex("0200000828020090"))
    assert resp.message_type == 0x02
    assert resp.destination == 0x28
    assert resp.command == 1
    assert resp.name == "charge_status"
    assert resp.success is False
