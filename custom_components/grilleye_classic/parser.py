"""Strict, dependency-free decoder for the observed Classic advertisement format."""

from dataclasses import dataclass
import re
import struct


def normalize_address(address: str) -> str:
    """Validate and normalize a Bluetooth MAC without silently removing garbage."""
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", address):
        raise ValueError("Expected a colon-separated Bluetooth MAC")
    return address.upper()


@dataclass(frozen=True)
class Reading:
    """The two verified probe fields; other bytes remain uninterpreted."""

    probe_1: float | None
    probe_2: float | None


def parse_payload(payload: bytes, address: str) -> Reading | None:
    """Decode manufacturer_data[0], excluding the BLE company ID itself.

    Require the observed 20-byte layout, prefix and embedded device address.
    Zero/FFFF are conservatively treated as no usable reading, not as 0 °C.
    These sentinel meanings still need a physical unplug/cold-probe test.
    """
    if len(payload) != 20 or payload[:2] != b"\x00\x00":
        return None
    try:
        expected = bytes.fromhex(normalize_address(address).replace(":", ""))
    except ValueError:
        return None
    if payload[2:8] != expected:
        return None
    values = struct.unpack_from("<HH", payload, 8)
    return Reading(*(None if value in (0, 0xFFFF) else value / 10 for value in values))


def payload_from_raw(raw: bytes) -> bytes | None:
    """Extract company 0 data from this packet, never a merged previous frame."""
    offset = 0
    result = None
    while offset < len(raw):
        length = raw[offset]
        if length == 0:
            break
        end = offset + length + 1
        if end > len(raw):
            return None
        if raw[offset + 1] == 0xFF:
            if length < 3:
                return None
            if raw[offset + 2 : offset + 4] == b"\x00\x00":
                if result is not None:
                    return None
                result = raw[offset + 4 : end]
        offset = end
    return result
