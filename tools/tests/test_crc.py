"""Password hash test vectors, computed against opencarwings@3927dad."""

import pytest

from carwings.crc import password_hash


@pytest.mark.parametrize(
    "password,expected",
    [
        ("", "5E90EF87"),
        ("test", "5F53E6C7"),
        ("password", "BC9E25D6"),
        ("LEAF2015!", "BFD5C0F0"),
    ],
)
def test_password_hash_vectors(password, expected):
    assert password_hash(password) == expected


def test_password_too_long_rejected():
    with pytest.raises(ValueError):
        password_hash("x" * 17)
