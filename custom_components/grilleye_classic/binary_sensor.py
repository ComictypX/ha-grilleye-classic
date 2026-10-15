"""Measurement-stream connectivity, not a GATT connection."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GrillEyeConfigEntry
from .entity import GrillEyeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: GrillEyeConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([GrillEyeConnectivity(entry.runtime_data, "receiving")])


class GrillEyeConnectivity(GrillEyeEntity, BinarySensorEntity):
    """Remain available and turn off when valid packets stop arriving."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "receiving"

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.fresh

    @property
    def extra_state_attributes(self):
        return {"source": self.coordinator.data.source, "stale_timeout": self.coordinator.timeout}
