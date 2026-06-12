"""Minimal TCP client that impersonates a TCU against a CARWINGS server.

This is the Phase 0 integration tool: point it at a running test_server.py
(nissan-leaf-tcu/scripts) or a local OpenCARWINGS tcuserver and confirm our
packets are accepted and parsed correctly.
"""

from __future__ import annotations

import socket
from contextlib import contextmanager

from carwings.protocol import (
    BodyType,
    EvInfo,
    GpsFix,
    TcuIdentity,
    ServerResponse,
    build_data_packet,
    build_init_packet,
    parse_response,
)

DEFAULT_PORT = 55230


class TcuClient:
    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    @contextmanager
    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        self._sock = sock
        try:
            yield self
        finally:
            sock.close()
            self._sock = None

    def _send(self, packet: bytes) -> bytes:
        assert self._sock is not None, "use within `with client.connect():`"
        self._sock.sendall(packet)
        try:
            return self._sock.recv(1024)
        except socket.timeout:
            return b""

    def send_init(self, identity: TcuIdentity, gps: GpsFix | None = None) -> ServerResponse | None:
        reply = self._send(build_init_packet(identity, gps))
        return parse_response(reply) if reply else None

    def send_data(
        self,
        identity: TcuIdentity,
        body_type: BodyType,
        ev_info: EvInfo,
        gps: GpsFix | None = None,
    ) -> bytes:
        return self._send(build_data_packet(identity, body_type, ev_info, gps))
