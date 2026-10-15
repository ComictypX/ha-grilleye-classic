"""Enable optional channels after their first usable positive live measurement."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import GrillEyeCoordinator


@callback
def async_watch_optional_probes(
    hass: HomeAssistant, entry: ConfigEntry[GrillEyeCoordinator], coordinator: GrillEyeCoordinator,
) -> None:
    """Respect user/device/system disables and retain identities and history.

    HA applies registry enablement with its normal delayed config-entry reload.
    Do not disable the channel again if measurements disappear afterwards.
    """
    registry = er.async_get(hass)

    @callback
    def detect() -> None:
        data = coordinator.data
        if entry.pref_disable_new_entities or not data.fresh or data.reading is None:
            return
        for index in range(3, 7):
            value = getattr(data.reading, f"probe_{index}")
            # Null slots can also mean unused inputs, even with zero_is_valid.
            if value is None or value <= 0:
                continue
            entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{coordinator.address}_probe_{index}")
            entity = registry.async_get(entity_id) if entity_id else None
            if (
                entity is not None
                and entity.config_entry_id == entry.entry_id
                and entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION
            ):
                registry.async_update_entity(entity.entity_id, disabled_by=None)

    entry.async_on_unload(coordinator.async_add_listener(detect))
    # A live packet may have arrived while the platforms were being set up.
    detect()
