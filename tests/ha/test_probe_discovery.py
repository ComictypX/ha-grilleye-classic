"""Exercise automatic channel activation through the real HA entity registry."""

from datetime import timedelta
import struct

import pytest

from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .test_integration import ADDRESS, DOMAIN, PAYLOAD, packet, setup_device


def probe_id(registry, index):
    return registry.async_get_entity_id("sensor", DOMAIN, f"{ADDRESS}_probe_{index}")


def receive(bluetooth_mock, values):
    payload = PAYLOAD[:8] + struct.pack("<6h", *values)
    bluetooth_mock[1].call_args.args[1](packet(manufacturer_data={0: payload}))


async def test_optional_channels_activate_on_positive_live_values(hass, bluetooth_mock):
    entry = await setup_device(hass)
    registry = er.async_get(hass)
    original = {index: probe_id(registry, index) for index in range(1, 7)}
    receive(bluetooth_mock, (360, 1070, 1234, 456, 789, 3000))
    await hass.async_block_till_done()
    for index in range(3, 7):
        assert registry.async_get(original[index]).disabled_by is None
    # HA uses its standard delayed reload to instantiate newly enabled entities.
    previous = entry.runtime_data
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert entry.runtime_data is not previous
    receive(bluetooth_mock, (360, 1070, 1234, 456, 789, 3000))
    await hass.async_block_till_done()
    for index, expected in enumerate((36.0, 107.0, 123.4, 45.6, 78.9, 300.0), 1):
        assert probe_id(registry, index) == original[index]
        assert hass.states.get(original[index]).state == str(expected)


@pytest.mark.parametrize("zero_is_valid", [False, True])
async def test_zero_and_invalid_values_do_not_activate(hass, bluetooth_mock, zero_is_valid):
    await setup_device(hass, {"zero_is_valid": zero_is_valid})
    registry = er.async_get(hass)
    receive(bluetooth_mock, (360, 1070, 0, -1, 32767, 3001))
    await hass.async_block_till_done()
    for index in range(3, 7):
        assert registry.async_get(probe_id(registry, index)).disabled_by is er.RegistryEntryDisabler.INTEGRATION


@pytest.mark.parametrize("disabled_by", [er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.DEVICE, er.RegistryEntryDisabler.CONFIG_ENTRY])
async def test_explicit_disables_are_preserved(hass, bluetooth_mock, disabled_by):
    await setup_device(hass)
    registry = er.async_get(hass)
    entity_id = probe_id(registry, 3)
    registry.async_update_entity(entity_id, disabled_by=disabled_by, name="Mein Fühler")
    receive(bluetooth_mock, (360, 1070, 1234, 0, 0, 0))
    await hass.async_block_till_done()
    entity = registry.async_get(entity_id)
    assert entity.disabled_by is disabled_by
    assert entity.name == "Mein Fühler"


async def test_disable_new_entities_preference_is_preserved(hass, bluetooth_mock):
    entry = await setup_device(hass)
    hass.config_entries.async_update_entry(entry, pref_disable_new_entities=True)
    receive(bluetooth_mock, (360, 1070, 1234, 0, 0, 0))
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert registry.async_get(probe_id(registry, 3)).disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_activated_channel_stays_enabled_when_unplugged_or_reloaded(hass, bluetooth_mock):
    entry = await setup_device(hass)
    registry = er.async_get(hass)
    entity_id = probe_id(registry, 3)
    receive(bluetooth_mock, (360, 1070, 1234, 0, 0, 0))
    await hass.async_block_till_done()
    assert registry.async_get(entity_id).disabled_by is None
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    receive(bluetooth_mock, (360, 1070, 0, 0, 0, 0))
    await hass.async_block_till_done()
    assert registry.async_get(entity_id).disabled_by is None
    assert hass.states.get(entity_id).state == "unavailable"


async def test_stale_and_unloaded_coordinator_cannot_activate_channels(hass, bluetooth_mock):
    entry = await setup_device(hass)
    coordinator = entry.runtime_data
    registry = er.async_get(hass)
    # A stale or replayed frame is rejected by the receiver before discovery.
    bluetooth_mock[1].call_args.args[1](packet(time=0, manufacturer_data={0: PAYLOAD[:8] + struct.pack("<6h", 360, 1070, 1234, 0, 0, 0)}))
    await hass.async_block_till_done()
    assert registry.async_get(probe_id(registry, 3)).disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert await hass.config_entries.async_unload(entry.entry_id)
    coordinator._async_received(packet(manufacturer_data={0: PAYLOAD[:8] + struct.pack("<6h", 360, 1070, 1234, 0, 0, 0)}))
    await hass.async_block_till_done()
    assert registry.async_get(probe_id(registry, 3)).disabled_by is er.RegistryEntryDisabler.INTEGRATION
    coordinator.async_stop()
