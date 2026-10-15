"""Strict, dependency-free decoder for the observed Classic advertisement format."""

from dataclasses import dataclass, field
import re
import struct


def normalize_address(address: str) -> str:
    """Validate and normalize a Bluetooth MAC without silently removing garbage."""
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", address):
        raise ValueError("Expected a colon-separated Bluetooth MAC")
    return address.upper()


@dataclass(frozen=True)
class Reading:
    """Six signed probe fields, retaining raw values for troubleshooting."""

    probe_1: float | None
    probe_2: float | None
    probe_3: float | None = None
    probe_4: float | None = None
    probe_5: float | None = None
    probe_6: float | None = None
    raw_values: tuple[int, ...] = field(default=(), compare=False)


def parse_payload(
    payload: bytes, address: str, *, zero_is_valid: bool = False,
) -> Reading | None:
    """Decode manufacturer_data[0], excluding the BLE company ID itself.

    Require the observed 20-byte layout, prefix and embedded device address.
    The APK confirms six signed int16 values in tenths of Celsius. Integration
    policy accepts raw 0..300 °C, retaining tenths rather than rounding like the
    app. Zero stays opt-in until unplug behavior/firmware is measured. Neither
    zero nor FFFF is claimed to be a hardware sentinel.
    """
    if len(payload) != 20 or payload[:2] != b"\x00\x00":
        return None
    try:
        expected = bytes.fromhex(normalize_address(address).replace(":", ""))
    except ValueError:
        return None
    if payload[2:8] != expected:
        return None
    values = struct.unpack_from("<6h", payload, 8)
    return Reading(*(
        value / 10 if 0 <= value <= 3000 and (value != 0 or zero_is_valid) else None
        for value in values
    ), raw_values=values)


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
