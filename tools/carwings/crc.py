"""Password hashing used by the CARWINGS server authentication.

The server calls this a "modified CRC-32", but it is the standard CRC-32
(reflected polynomial 0xEDB88320, init 0xFFFFFFFF, final XOR 0xFFFFFFFF)
computed over the password with the literal suffix b"evtelematics"
appended. The result is rendered as 8 uppercase hexadecimal characters.

Verified against opencarwings@3927dad tculink/utils/password_hash.py.
Test vectors (see tests/test_crc.py):
    ""          -> 5E90EF87
    "test"      -> 5F53E6C7
    "password"  -> BC9E25D6
"""

import binascii

PASSWORD_SUFFIX = b"evtelematics"
MAX_PASSWORD_LEN = 16


def crc32(data: bytes) -> int:
    """Standard CRC-32 over ``data + PASSWORD_SUFFIX``."""
    return binascii.crc32(data + PASSWORD_SUFFIX) & 0xFFFFFFFF


def password_hash(password: str) -> str:
    """Return the 8-char uppercase hex hash the TCU sends for ``password``."""
    if len(password) > MAX_PASSWORD_LEN:
        raise ValueError(
            f"password exceeds {MAX_PASSWORD_LEN} characters"
        )
    return "{:08X}".format(crc32(password.encode("ascii")))
