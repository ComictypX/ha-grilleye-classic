"""GrillEye Classic passive Bluetooth integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_STALE_TIMEOUT, CONF_ZERO_IS_VALID, DEFAULT_STALE_TIMEOUT
from .coordinator import GrillEyeCoordinator
from .discovery import async_watch_optional_probes

type GrillEyeConfigEntry = ConfigEntry[GrillEyeCoordinator]
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: GrillEyeConfigEntry) -> bool:
    """Set up one device, even if it is currently switched off."""
    coordinator = GrillEyeCoordinator(
        hass, entry.data[CONF_ADDRESS],
        entry.options.get(CONF_STALE_TIMEOUT, DEFAULT_STALE_TIMEOUT),
        zero_is_valid=entry.options.get(CONF_ZERO_IS_VALID, False),
    )
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_watch_optional_probes(hass, entry, coordinator)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: GrillEyeConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GrillEyeConfigEntry) -> bool:
    """Unload entities; registered cleanup runs when the unload succeeds."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
