"""Temperature and reception diagnostics."""

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GrillEyeConfigEntry
from .coordinator import GrillEyeCoordinator
from .entity import GrillEyeEntity

DESCRIPTIONS = (
    SensorEntityDescription(
        key="probe_1", translation_key="probe_1", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="probe_2", translation_key="probe_2", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="rssi", translation_key="rssi", device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_seen", translation_key="last_seen", device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GrillEyeConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(GrillEyeSensor(entry.runtime_data, desc) for desc in DESCRIPTIONS)


class GrillEyeSensor(GrillEyeEntity, SensorEntity):
    """Expose usable readings only while the measurement stream is fresh."""

    def __init__(self, coordinator: GrillEyeCoordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.key == "last_seen":
            return True
        return self.coordinator.data.fresh and self.native_value is not None

    @property
    def native_value(self):
        data = self.coordinator.data
        key = self.entity_description.key
        if key in ("probe_1", "probe_2"):
            return getattr(data.reading, key) if data.reading else None
        return getattr(data, key)
