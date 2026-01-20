"""Sensor platform for Antel Consumo integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AntelConsumoCoordinator
from .antel_scraper import AntelConsumoData


@dataclass(frozen=True, kw_only=True)
class AntelSensorEntityDescription(SensorEntityDescription):
    """Describes an Antel sensor entity."""

    value_fn: Callable[[AntelConsumoData], Any]


SENSORS: tuple[AntelSensorEntityDescription, ...] = (
    AntelSensorEntityDescription(
        key="used_data",
        translation_key="used_data",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download",
        value_fn=lambda data: data.used_data_gb,
    ),
    AntelSensorEntityDescription(
        key="total_data",
        translation_key="total_data",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:database",
        value_fn=lambda data: data.total_data_gb,
    ),
    AntelSensorEntityDescription(
        key="remaining_data",
        translation_key="remaining_data",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:database-check",
        value_fn=lambda data: data.remaining_data_gb,
    ),
    AntelSensorEntityDescription(
        key="percentage_used",
        translation_key="percentage_used",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent",
        value_fn=lambda data: round(data.percentage_used, 1) if data.percentage_used is not None else None,
    ),
    AntelSensorEntityDescription(
        key="plan_name",
        translation_key="plan_name",
        icon="mdi:file-document",
        value_fn=lambda data: data.plan_name,
    ),
    AntelSensorEntityDescription(
        key="billing_period",
        translation_key="billing_period",
        icon="mdi:calendar",
        value_fn=lambda data: data.billing_period,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Antel Consumo sensors based on a config entry."""
    coordinator: AntelConsumoCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AntelSensor(coordinator, description, entry)
        for description in SENSORS
    )


class AntelSensor(CoordinatorEntity[AntelConsumoCoordinator], SensorEntity):
    """Representation of an Antel Consumo sensor."""

    entity_description: AntelSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AntelConsumoCoordinator,
        description: AntelSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Antel Internet",
            "manufacturer": "Antel",
            "model": "Mi Antel",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.coordinator.data is None or self.coordinator.data.raw_data is None:
            return None

        # Only add raw data for the main sensor (used_data)
        if self.entity_description.key == "used_data":
            return {"raw_data": self.coordinator.data.raw_data}

        return None
