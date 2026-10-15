"""Offline parser tests; no Home Assistant dependency or emulated decoder."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "grilleye_parser", ROOT / "custom_components/grilleye_classic/parser.py",
)
parser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = parser
SPEC.loader.exec_module(parser)
ADDRESS = "40:06:A0:8B:40:01"
CURRENT = bytes.fromhex("00004006a08b400168012e040000000000000000")
PREVIOUS = bytes.fromhex("00004006a08b4001400138040000000000000000")
RAW = bytes.fromhex("0201060302f0ff17ff000000004006a08b400168012e040000000000000000")


class ParserTests(unittest.TestCase):
    def test_current_capture(self):
        self.assertEqual(parser.parse_payload(CURRENT, ADDRESS), parser.Reading(36.0, 107.0))

    def test_previous_capture(self):
        self.assertEqual(parser.parse_payload(PREVIOUS, ADDRESS), parser.Reading(32.0, 108.0))

    def test_raw_capture_strips_company_id_once(self):
        self.assertEqual(parser.payload_from_raw(RAW), CURRENT)

    def test_truncated_and_extended_payloads(self):
        for size in range(20):
            with self.subTest(size=size):
                self.assertIsNone(parser.parse_payload(CURRENT[:size], ADDRESS))
        self.assertIsNone(parser.parse_payload(CURRENT + b"\0", ADDRESS))

    def test_wrong_device_prefix_and_company_prefix(self):
        self.assertIsNone(parser.parse_payload(CURRENT, "40:06:A0:8B:40:02"))
        self.assertIsNone(parser.parse_payload(b"\1" + CURRENT[1:], ADDRESS))
        self.assertIsNone(parser.parse_payload(b"\0\0" + CURRENT, ADDRESS))

    def test_address_validation(self):
        self.assertEqual(parser.normalize_address(ADDRESS.lower()), ADDRESS)
        for address in ("", "4006a08b4001", "40:06:A0:8B:40:0G", ADDRESS + "x"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                parser.normalize_address(address)
        self.assertIsNone(parser.parse_payload(CURRENT, "invalid"))

    def test_each_probe_missing_independently(self):
        for missing in (0, 0xFFFF):
            for index in (0, 1):
                payload = bytearray(CURRENT)
                struct.pack_into("<H", payload, 8 + 2 * index, missing)
                result = parser.parse_payload(bytes(payload), ADDRESS)
                self.assertIsNone((result.probe_1, result.probe_2)[index])
                self.assertEqual((result.probe_1, result.probe_2)[1-index], (107, 36)[index])

    def test_unsigned_little_endian_and_tenths(self):
        payload = bytearray(CURRENT)
        struct.pack_into("<HH", payload, 8, 1234, 32768)
        self.assertEqual(parser.parse_payload(bytes(payload), ADDRESS), parser.Reading(123.4, 3276.8))

    def test_unknown_tail_does_not_become_more_probes(self):
        self.assertEqual(parser.parse_payload(CURRENT[:12] + b"\xff" * 8, ADDRESS), parser.Reading(36, 107))

    def test_raw_malformed_unrelated_duplicate(self):
        for raw in (b"", b"\0", RAW[:-1], b"\x02\xff\x00", b"\x03\xff\x01\x00", RAW + RAW):
            with self.subTest(raw=raw):
                self.assertIsNone(parser.payload_from_raw(raw))


if __name__ == "__main__":
    unittest.main()
