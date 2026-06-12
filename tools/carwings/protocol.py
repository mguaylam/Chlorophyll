"""CARWINGS TCU->server packet construction and response parsing.

Byte layout verified by reading opencarwings@3927dad
(tculink/gdc_proto/{parser,datafields,responses}.py). See
docs/protocol-server.md for the annotated specification.

Scope (Phase 0): enough to make a real server accept an INIT (logon) packet
and parse a DATA (telemetry) packet. The EV-info body encoder covers the
high-value fields (SOC, GIDs, plug/charge/AC state); rarer bitfields are
left zeroed and marked TODO until exercised against a live capture.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum

from carwings.crc import password_hash

# --- Header geometry (offsets into the packet) -----------------------------
# Common to packet types 1 and 3. Verified against parser.parse_gdc_packet
# and datafields.parse_tcu_info / parse_auth_info.
TCU_INFO_LEN = 100          # bytes [0:100]
BODY_TYPE_OFFSET = 100      # byte [100]
ENV_OFFSET = 101            # bytes [101:119], GPS starts at +2
GPS_OFFSET = 103            # bytes [103:119]
AUTH_OFFSET = 119           # bytes [119:153]
BODY_OFFSET = 153           # type-3 EV info body starts here
HEADER_END = 153

# Field slices inside the 100-byte TCU info block.
_VEH_DESCRIPTOR = 1
_VEH_CODES = slice(4, 8)
_VIN = slice(9, 26)         # 17 ASCII
_TCU_ID = slice(27, 39)     # 12 ASCII (model)
_MSN = slice(40, 55)        # 15 ASCII
_UNIT_ID = slice(56, 68)    # 12 ASCII (navi serial)
_ICCID = slice(69, 89)      # 20 ASCII
_SW_VERSION = slice(90, 99)  # 9 ASCII

# Auth block is bytes [119:153]; inside it, user at +1, pass at +18.
_AUTH_USER = slice(AUTH_OFFSET + 1, AUTH_OFFSET + 16)   # 15 ASCII
_AUTH_PASS = slice(AUTH_OFFSET + 18, AUTH_OFFSET + 33)  # 15 ASCII

# Vehicle descriptor byte: AZE0 (2013+) reports 0x92, ZE0 reports 0x02.
VEHICLE_DESCRIPTOR_AZE0 = 0x92
VEHICLE_DESCRIPTOR_ZE0 = 0x02


class PacketType(IntEnum):
    INIT = 0x01      # logon / command poll
    DATA = 0x03      # telemetry + event reports
    CONFIG = 0x05    # TCU configuration dump


class BodyType(IntEnum):
    LOGON = 0x27
    CHARGE_STATUS = 0x28
    CP_REMIND = 0x29       # charging cable unplugged
    REMOTE_STOP = 0x2A
    CHARGE_RESULT = 0x2B
    AC_RESULT = 0x2C
    CONFIG_READ = 0x2E
    BATTERY_HEAT = 0x2F


def _ascii_field(value: str, width: int) -> bytes:
    """Encode ``value`` as NUL-padded ASCII of exactly ``width`` bytes."""
    raw = value.encode("ascii")
    if len(raw) > width:
        raise ValueError(f"{value!r} does not fit in {width} bytes")
    return raw + b"\x00" * (width - len(raw))


@dataclass
class TcuIdentity:
    """Identity fields the server matches a registered car against.

    The server keys on the VIN, then checks tcu_model (tcu_id), navi serial
    (unit_id) and iccid before accepting username OR password hash.
    """

    vin: str
    tcu_model: str           # e.g. "GNOV1N..." — server field tcu_model
    unit_id: str             # navi unit serial
    iccid: str               # SIM ICCID
    username: str
    password: str
    sw_version: str = "06.42R"
    msn: str = ""
    vehicle_descriptor: int = VEHICLE_DESCRIPTOR_AZE0
    vehicle_codes: bytes = b"\x00\x00\x00\x00"

    def tcu_info_block(self, body_type: BodyType) -> bytes:
        buf = bytearray(TCU_INFO_LEN)
        buf[_VEH_DESCRIPTOR] = self.vehicle_descriptor
        buf[_VEH_CODES] = self.vehicle_codes
        buf[_VIN] = _ascii_field(self.vin, 17)
        buf[_TCU_ID] = _ascii_field(self.tcu_model, 12)
        buf[_MSN] = _ascii_field(self.msn, 15)
        buf[_UNIT_ID] = _ascii_field(self.unit_id, 12)
        buf[_ICCID] = _ascii_field(self.iccid, 20)
        buf[_SW_VERSION] = _ascii_field(self.sw_version, 9)
        return bytes(buf)

    def auth_block(self) -> bytes:
        buf = bytearray(34)  # bytes [119:153]
        buf[1:16] = _ascii_field(self.username, 15)
        buf[18:33] = _ascii_field(password_hash(self.password), 15)
        return bytes(buf)


@dataclass
class GpsFix:
    """A GPS fix encoded the way parse_gps_info expects (deg/min/sec*100)."""

    latitude: float
    longitude: float
    valid: bool = True
    home: bool = False

    def encode(self) -> bytes:
        buf = bytearray(16)  # bytes [103:119]; parser reads indices 5..13
        lat, lon = self.latitude, self.longitude
        lat_mode = 0 if lat >= 0 else 1   # 0=N, 1=S
        lon_mode = 0 if lon >= 0 else 1   # 0=E, 1=W
        flags = 0
        flags |= (1 if self.valid else 0) << 7
        flags |= lat_mode << 5
        flags |= lon_mode << 4
        flags |= (0 if self.home else 1) << 3  # home==0 means "at home"
        buf[5] = flags
        for base, value in ((6, abs(lat)), (10, abs(lon))):
            deg = int(value)
            minutes = int((value - deg) * 60)
            seconds = (value - deg - minutes / 60) * 3600
            buf[base] = deg & 0xFF
            buf[base + 1] = minutes & 0xFF
            struct.pack_into(">H", buf, base + 2, int(round(seconds * 100)) & 0xFFFF)
        return bytes(buf)


@dataclass
class EvInfo:
    """Telemetry for a type-3 DATA packet.

    Only the commonly used fields are encoded; the bit positions follow
    datafields.parse_evinfo. Fields not set here are left zero.
    TODO(phase0): cover charge-time estimates and battery-heater bits once a
    real capture is available to check the packing.
    """

    soc: float = 0.0          # 0..100 %, encoded as soc*20 across 11 bits
    gids: int = 0             # 0..1023
    soh: int = 0              # 0..100 %
    plugged_in: bool = False
    charging: bool = False
    quick_charging: bool = False
    ac_on: bool = False
    ignition: bool = False
    range_acon: int = 0       # raw byte
    range_acoff: int = 0      # raw byte

    def encode(self) -> bytes:
        # The body layout is a length-prefixed range block then an EV block.
        # We emit a fixed 24-byte body matching the indices parse_evinfo reads.
        body = bytearray(24)
        body[0] = 0x06            # rangeinfo_len (informational)
        body[2] = self.range_acon & 0xFF
        body[4] = self.range_acoff & 0xFF
        body[8] = 0x0C            # evinfo_len (informational)

        charge_state = 0
        if self.quick_charging:
            charge_state = 2
        elif self.charging:
            charge_state = 1
        b9 = 0
        b9 |= (charge_state & 0b11) << 6
        b9 |= (1 if self.ignition else 0) << 5
        b9 |= (1 if self.ac_on else 0) << 1
        b9 |= (1 if self.plugged_in else 0)
        body[9] = b9

        gids = self.gids & 0x3FF
        body[14] = (gids >> 2) & 0xFF
        body[15] = ((gids & 0b11) << 6) | ((self.soh >> 1) & 0b111111)

        soc_raw = int(round(self.soc * 20)) & 0x7FF  # 11 bits
        body[16] = ((self.soh & 1) << 7) | ((soc_raw >> 4) & 0x7F)
        body[17] = (soc_raw & 0xF) << 4
        return bytes(body)


def _frame_header(packet_type: PacketType, total_len: int, descriptor: int) -> bytearray:
    """First bytes shared by request packets: type, descriptor, direction, len."""
    buf = bytearray()
    buf.append(int(packet_type))
    buf.append(descriptor)
    buf.append(0x00)  # direction: 0 = request (TCU -> server)
    buf += struct.pack(">H", total_len)
    return buf


def build_init_packet(identity: TcuIdentity, gps: GpsFix | None = None) -> bytes:
    """Build a type-1 INIT (logon) packet: identity + auth + GPS, no body.

    Header bytes 0..2 carry type/descriptor/direction (the "01 02 00" prefix
    test_server keys on); byte 100 is the body type. The parser reads identity
    from bytes [0:100], GPS from [103:119] and auth from [119:153].
    """
    packet = bytearray(HEADER_END)
    packet[0:TCU_INFO_LEN] = identity.tcu_info_block(BodyType.LOGON)
    packet[0] = int(PacketType.INIT)
    packet[_VEH_DESCRIPTOR] = identity.vehicle_descriptor
    packet[2] = 0x00
    packet[BODY_TYPE_OFFSET] = int(BodyType.LOGON)
    packet[GPS_OFFSET:GPS_OFFSET + 16] = (gps or GpsFix(0.0, 0.0, valid=False)).encode()
    packet[AUTH_OFFSET:AUTH_OFFSET + 34] = identity.auth_block()
    return bytes(packet)


def build_data_packet(
    identity: TcuIdentity,
    body_type: BodyType,
    ev_info: EvInfo,
    gps: GpsFix | None = None,
) -> bytes:
    """Build a type-3 DATA packet carrying telemetry/event body."""
    packet = bytearray(HEADER_END)
    packet[0:TCU_INFO_LEN] = identity.tcu_info_block(body_type)
    packet[0] = int(PacketType.DATA)
    packet[_VEH_DESCRIPTOR] = identity.vehicle_descriptor
    packet[2] = 0x00
    packet[BODY_TYPE_OFFSET] = int(body_type)
    packet[GPS_OFFSET:GPS_OFFSET + 16] = (gps or GpsFix(0.0, 0.0, valid=False)).encode()
    packet[AUTH_OFFSET:AUTH_OFFSET + 34] = identity.auth_block()
    packet += ev_info.encode()
    return bytes(packet)


@dataclass
class ServerResponse:
    """A parsed type-2 command response (server -> TCU)."""

    raw: bytes
    message_type: int
    destination: int
    command: int
    success: bool

    COMMANDS = {
        (0x28, 0x01): "charge_status",
        (0x2B, 0x02): "charge_request",
        (0x2C, 0x03): "ac_on",
        (0x2C, 0x04): "ac_off",
    }

    @property
    def name(self) -> str:
        return self.COMMANDS.get((self.destination, self.command), "unknown")


def parse_response(data: bytes) -> ServerResponse:
    """Parse an 8-byte type-2 response: 02 00 <len:u16> <dest> 02 00 <cmd>."""
    if len(data) < 8:
        raise ValueError(f"response too short: {data.hex()}")
    message_type = data[0]
    destination = data[4]
    command_byte = data[7]
    failure = bool((command_byte >> 7) & 1)
    command = (command_byte >> 4) & 0b111
    return ServerResponse(
        raw=data,
        message_type=message_type,
        destination=destination,
        command=command,
        success=not failure,
    )
