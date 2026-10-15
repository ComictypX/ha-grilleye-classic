"""Real config-entry, entity, discovery, options and unload tests on Linux."""

from datetime import timedelta
from types import SimpleNamespace
import struct
import pytest

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

DOMAIN = "grilleye_classic"
ADDRESS = "40:06:A0:8B:40:01"
PAYLOAD = bytes.fromhex("00004006a08b400168012e040000000000000000")


async def setup_device(hass, options=None):
    entry = MockConfigEntry(domain=DOMAIN, title="GrillEye Classic 4001", unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}, options=options or {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def packet(**kwargs):
    data = dict(address=ADDRESS, time=bluetooth.MONOTONIC_TIME(), rssi=-60,
                source="shelly", manufacturer_data={0: PAYLOAD}, raw=None)
    data.update(kwargs)
    return SimpleNamespace(**data)


async def test_entities_timeout_recovery_unload(hass, bluetooth_mock):
    entry = await setup_device(hass)
    changed, packets = bluetooth_mock
    assert changed.call_args.args[2] == {"address": ADDRESS, "connectable": False}
    assert changed.call_args.args[3] == bluetooth.BluetoothScanningMode.PASSIVE
    registry = er.async_get(hass)
    ids = {key: registry.async_get_entity_id(domain, DOMAIN, f"{ADDRESS}_{key}") for domain, key in (
        ("sensor", "probe_1"), ("sensor", "probe_2"), ("sensor", "rssi"),
        ("sensor", "last_seen"), ("binary_sensor", "receiving"),
    )}
    assert hass.states.get(ids["probe_1"]).state == "unavailable"
    assert hass.states.get(ids["receiving"]).state == "off"
    receive = packets.call_args.args[1]
    first = packet()
    receive(first)
    await hass.async_block_till_done()
    assert hass.states.get(ids["probe_1"]).state == "36.0"
    assert hass.states.get(ids["probe_2"]).state == "107.0"
    assert hass.states.get(ids["rssi"]).state == "-60"
    assert hass.states.get(ids["receiving"]).state == "on"
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=121))
    await hass.async_block_till_done()
    assert hass.states.get(ids["probe_1"]).state == "unavailable"
    assert hass.states.get(ids["receiving"]).state == "off"
    assert hass.states.get(ids["last_seen"]).state not in ("unknown", "unavailable")
    receive(packet(time=first.time + 0.01, source="second_proxy"))
    await hass.async_block_till_done()
    assert hass.states.get(ids["receiving"]).state == "on"
    assert await hass.config_entries.async_unload(entry.entry_id)
    changed.return_value.assert_called_once()
    packets.return_value.assert_called_once()


async def test_missing_probe_does_not_hide_other(hass, bluetooth_mock):
    await setup_device(hass)
    bluetooth_mock[1].call_args.args[1](packet(manufacturer_data={0: PAYLOAD[:8] + b"\0\0" + PAYLOAD[10:]}))
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    probe1 = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_1")
    probe2 = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_2")
    assert hass.states.get(probe1).state == "unavailable"
    assert hass.states.get(probe2).state == "107.0"


async def test_manual_flow_offline_and_duplicate(hass, bluetooth_mock):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    invalid = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_ADDRESS: "bad"})
    assert invalid["errors"] == {CONF_ADDRESS: "invalid_address"}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_ADDRESS: ADDRESS.lower()})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_ADDRESS: ADDRESS}
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER}, data={CONF_ADDRESS: ADDRESS})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_bluetooth_discovery_and_reject(hass, bluetooth_mock):
    info = packet(service_uuids=["0000fff0-0000-1000-8000-00805f9b34fb"])
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=info)
    assert result["step_id"] == "confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_BLUETOOTH}, data=packet(service_uuids=[]))
    assert result["reason"] == "not_supported"


async def test_options_validate_and_reload(hass, bluetooth_mock):
    entry = await setup_device(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    # The real flow manager validates the form before calling the options step.
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(result["flow_id"], {"stale_timeout": 1})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"stale_timeout": 60})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.timeout == 60


async def test_optional_probes_keep_existing_unique_ids(hass, bluetooth_mock):
    entry = await setup_device(hass)
    registry = er.async_get(hass)
    for index in range(1, 7):
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_{index}")
        entity = registry.async_get(entity_id)
        assert entity.config_entry_id == entry.entry_id
        assert entity.disabled_by == (None if index <= 2 else er.RegistryEntryDisabler.INTEGRATION)
        if index >= 3:
            assert hass.states.get(entity_id) is None
            registry.async_update_entity(entity_id, disabled_by=None)
    # Reload applies the registry's explicit channel opt-in without changing IDs.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    payload = PAYLOAD[:8] + struct.pack("<6h", 361, 1071, 1234, 456, 789, 2999)
    bluetooth_mock[1].call_args.args[1](packet(manufacturer_data={0: payload}))
    await hass.async_block_till_done()
    for index, expected in enumerate((36.1, 107.1, 123.4, 45.6, 78.9, 299.9), 1):
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_{index}")
        state = hass.states.get(entity_id)
        assert state.state == str(expected)
        assert state.attributes["value_status"] == "valid"
        assert state.attributes["raw_value"] == round(expected * 10)


async def test_signed_invalid_values_diagnostics_and_stale(hass, bluetooth_mock):
    await setup_device(hass)
    registry = er.async_get(hass)
    probe1 = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_1")
    probe2 = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_2")
    receiving = registry.async_get_entity_id("binary_sensor", DOMAIN, f"{ADDRESS}_receiving")
    assert hass.states.get(receiving).attributes["probes"]["probe_1"]["value_status"] == "no_packet"
    receive = bluetooth_mock[1].call_args.args[1]
    receive(packet(manufacturer_data={0: PAYLOAD[:8] + struct.pack("<6h", -1, 3001, 0, 0, 0, 0)}))
    await hass.async_block_till_done()
    for index, (entity_id, raw) in enumerate(((probe1, -1), (probe2, 3001)), 1):
        state = hass.states.get(entity_id)
        assert state.state == "unavailable"
        diagnostic = hass.states.get(receiving).attributes["probes"][f"probe_{index}"]
        assert diagnostic["value_status"] == "out_of_range"
        assert diagnostic["raw_value"] == raw
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=121))
    await hass.async_block_till_done()
    assert hass.states.get(receiving).attributes["probes"]["probe_1"]["value_status"] == "stale"


async def test_zero_option_reload_and_recovery(hass, bluetooth_mock):
    entry = await setup_device(hass)
    registry = er.async_get(hass)
    probe1 = registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_1")
    receiving = registry.async_get_entity_id("binary_sensor", DOMAIN, f"{ADDRESS}_receiving")
    zero_packet = PAYLOAD[:8] + b"\0\0" + PAYLOAD[10:]
    bluetooth_mock[1].call_args.args[1](packet(manufacturer_data={0: zero_packet}))
    await hass.async_block_till_done()
    assert hass.states.get(receiving).attributes["probes"]["probe_1"]["value_status"] == "zero_filtered"
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"stale_timeout": 60, "zero_is_valid": True})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.zero_is_valid is True
    assert hass.states.get(probe1).state == "unavailable"  # No cached measurement on reload.
    bluetooth_mock[1].call_args.args[1](packet(manufacturer_data={0: zero_packet}))
    await hass.async_block_till_done()
    assert hass.states.get(probe1).state == "0.0"
    assert hass.states.get(probe1).attributes["value_status"] == "valid"
