"""Exercise the production receiver with minimal HA boundary doubles.

These tests check timer/packet logic, not Home Assistant integration wiring.
The tests/ha suite checks the actual framework on Linux.
"""

from datetime import UTC, datetime
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "offline_grilleye"


class FakeCoordinator:
    def __class_getitem__(cls, item):
        return cls

    def __init__(self, hass, *args, **kwargs):
        self.hass = hass

    def async_set_updated_data(self, data):
        self.data = data


def module(name, **attrs):
    result = ModuleType(name)
    result.__dict__.update(attrs)
    return result


def load(name):
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.{name}", ROOT / f"custom_components/grilleye_classic/{name}.py",
    )
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        self.timers = []
        self.registrations = []
        self.cancelled = []

        def register(*args):
            self.registrations.append(args)
            return lambda: self.cancelled.append(args)

        def later(hass, delay, callback):
            timer = SimpleNamespace(delay=delay, callback=callback, cancelled=False)
            self.timers.append(timer)
            def cancel():
                timer.cancelled = True
            return cancel

        self.bt = SimpleNamespace(
            MONOTONIC_TIME=lambda: self.now,
            BluetoothScanningMode=SimpleNamespace(PASSIVE="passive"),
            async_register_callback=register,
            async_register_advertisement_callback=register,
            BluetoothServiceInfoBleak=object, BluetoothChange=object,
        )
        modules = {
            PACKAGE: module(PACKAGE, __path__=[]),
            "homeassistant": module("homeassistant"),
            "homeassistant.components": module("homeassistant.components", bluetooth=self.bt),
            "homeassistant.core": module("homeassistant.core", HomeAssistant=object, callback=lambda f: f),
            "homeassistant.helpers": module("homeassistant.helpers"),
            "homeassistant.helpers.event": module("homeassistant.helpers.event", async_call_later=later),
            "homeassistant.helpers.update_coordinator": module("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=FakeCoordinator),
            "homeassistant.util": module("homeassistant.util", dt=SimpleNamespace(utcnow=lambda: datetime(2026, 10, 15, tzinfo=UTC))),
        }
        self.context = patch.dict(sys.modules, modules)
        self.context.start()
        load("const")
        load("parser")
        self.receiver = load("coordinator").GrillEyeCoordinator(object(), "40:06:A0:8B:40:01", 120)
        self.addCleanup(self.context.stop)

    def packet(self, payload=None, **kwargs):
        data = dict(address="40:06:A0:8B:40:01", time=self.now, rssi=-60, source="shelly",
                    manufacturer_data={0: payload or bytes.fromhex("00004006a08b400168012e040000000000000000")}, raw=None)
        data.update(kwargs)
        return SimpleNamespace(**data)

    def test_start_is_passive_and_no_cached_reading(self):
        self.receiver.async_start()
        self.assertFalse(self.receiver.data.fresh)
        self.assertEqual(self.registrations[0][2], {"address": "40:06:A0:8B:40:01", "connectable": False})
        self.assertEqual(self.registrations[0][3], "passive")
        self.assertEqual(len(self.registrations), 2)

    def test_values_and_expiration(self):
        self.receiver._async_received(self.packet())
        self.assertTrue(self.receiver.data.fresh)
        self.assertEqual(self.receiver.data.reading.probe_1, 36)
        seen = self.receiver.data.last_seen
        self.timers[-1].callback(None)
        self.assertFalse(self.receiver.data.fresh)
        self.assertEqual(self.receiver.data.last_seen, seen)

    def test_identical_temperature_refreshes_deadline(self):
        self.receiver._async_received(self.packet())
        self.now += 100
        self.receiver._async_received(self.packet())
        self.assertTrue(self.timers[0].cancelled)
        self.assertEqual(self.timers[-1].delay, 120)
        self.assertTrue(self.receiver.data.fresh)

    def test_bad_frame_never_refreshes_timeout(self):
        self.receiver._async_received(self.packet())
        self.now += 100
        self.receiver._async_received(self.packet(b"bad"))
        self.assertEqual(len(self.timers), 1)
        self.assertFalse(self.timers[0].cancelled)

    def test_old_duplicate_future_wrong_address(self):
        for kwargs in ({"time": 879}, {"time": 1002}, {"address": "00:00:00:00:00:00"}):
            self.receiver._async_received(self.packet(**kwargs))
            self.assertFalse(self.receiver.data.fresh)
        self.receiver._async_received(self.packet())
        self.receiver._async_received(self.packet(time=999))
        self.receiver._async_received(self.packet())
        self.assertEqual(len(self.timers), 1)

    def test_age_reduces_deadline(self):
        self.receiver._async_received(self.packet(time=990))
        self.assertEqual(self.timers[0].delay, 110)

    def test_recovery_and_proxy_switch(self):
        self.receiver._async_received(self.packet())
        self.timers[-1].callback(None)
        self.now += 200
        self.receiver._async_received(self.packet(source="other shelly"))
        self.assertTrue(self.receiver.data.fresh)
        self.assertEqual(self.receiver.data.source, "other shelly")

    def test_raw_packet_beats_merged_manufacturer_history(self):
        self.receiver._async_received(self.packet(raw=b"\x02\x01\x06"))
        self.assertFalse(self.receiver.data.fresh)
        raw = bytes.fromhex("0201060302f0ff17ff000000004006a08b400168012e040000000000000000")
        self.receiver._async_received(self.packet(raw=raw, manufacturer_data={0: b"bad"}))
        self.assertTrue(self.receiver.data.fresh)

    def test_changed_cache_does_not_restore_freshness(self):
        self.receiver._async_changed(self.packet(), None)
        self.assertFalse(self.receiver.data.fresh)

    def test_unload_cleans_both_callbacks_and_timer(self):
        self.receiver.async_start()
        self.receiver._async_received(self.packet())
        self.receiver.async_stop()
        self.receiver.async_stop()
        self.assertEqual(len(self.cancelled), 2)
        self.assertTrue(self.timers[0].cancelled)

    def test_zero_policy_reaches_live_decoder(self):
        payload = bytes.fromhex("00004006a08b400100002e040000000000000000")
        self.receiver.zero_is_valid = True
        self.receiver._async_received(self.packet(payload))
        self.assertEqual(self.receiver.data.reading.probe_1, 0)
        self.assertEqual(self.receiver.data.reading.probe_6, 0)

    def test_diagnostics_explain_missing_filtered_invalid_and_stale(self):
        self.assertEqual(self.receiver.probe_diagnostics["probe_1"]["value_status"], "no_packet")
        self.receiver._async_received(self.packet())
        diagnostics = self.receiver.probe_diagnostics
        self.assertEqual(diagnostics["probe_1"], {"raw_value": 360, "value_status": "valid"})
        self.assertEqual(diagnostics["probe_6"], {"raw_value": 0, "value_status": "zero_filtered"})
        self.timers[-1].callback(None)
        self.assertEqual(self.receiver.probe_diagnostics["probe_6"]["value_status"], "stale")

    def test_valid_frame_with_invalid_channels_still_confirms_reception(self):
        payload = bytes.fromhex("00004006a08b4001") + b"\xff\xff" * 6
        self.receiver._async_received(self.packet(payload))
        self.assertTrue(self.receiver.data.fresh)
        self.assertIsNone(self.receiver.data.reading.probe_1)
        self.assertIsNone(self.receiver.data.reading.probe_6)
