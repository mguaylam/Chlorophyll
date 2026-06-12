"""Reference Python implementation of the TCU side of the CARWINGS protocol.

Phase 0 of Chlorophyll: validate the protocol understanding (packet framing,
field offsets, password hash) against a real server before writing any
firmware. See docs/protocol-server.md for the byte-level specification and
its verification status.

This is an original implementation derived from reading the OpenCARWINGS
server source (opencarwings@3927dad); it does not copy upstream code.
"""

from carwings.crc import password_hash
from carwings.protocol import (
    PacketType,
    BodyType,
    TcuIdentity,
    build_init_packet,
    build_data_packet,
    parse_response,
    ServerResponse,
)

__all__ = [
    "password_hash",
    "PacketType",
    "BodyType",
    "TcuIdentity",
    "build_init_packet",
    "build_data_packet",
    "parse_response",
    "ServerResponse",
]
