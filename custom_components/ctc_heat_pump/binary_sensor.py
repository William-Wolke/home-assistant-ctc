"""Binary sensors for the CTC Heat Pump integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import CtcDataUpdateCoordinator
from .entity import CtcEntity
from .model_support import is_compatible


@dataclass(frozen=True, kw_only=True)
class CtcBinarySensorDescription(BinarySensorEntityDescription):
    """CTC binary sensor description."""

    source_sensor_key: str
    value_fn: Callable[[CtcDataUpdateCoordinator], bool | None]


BINARY_SENSORS: tuple[CtcBinarySensorDescription, ...] = (
    CtcBinarySensorDescription(
        key="dhw_charge_active_binary",
        name="DHW charge active",
        device_class=BinarySensorDeviceClass.RUNNING,
        source_sensor_key="dhw_charge_active",
        value_fn=lambda coordinator: _bool_from_sensor(coordinator, "dhw_charge_active"),
    ),
    CtcBinarySensorDescription(
        key="dhw_extra_charge_binary",
        name="DHW extra charge",
        device_class=BinarySensorDeviceClass.RUNNING,
        source_sensor_key="dhw_extra_charge",
        value_fn=lambda coordinator: _bool_from_sensor(coordinator, "dhw_extra_charge"),
    ),
    CtcBinarySensorDescription(
        key="active_cooling_demand_binary",
        name="Active cooling demand",
        device_class=BinarySensorDeviceClass.RUNNING,
        source_sensor_key="active_cooling_demand",
        value_fn=lambda coordinator: _bool_from_sensor(coordinator, "active_cooling_demand"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CTC binary sensors."""
    coordinator: CtcDataUpdateCoordinator = entry.runtime_data
    async_add_entities(
        CtcBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
        if is_compatible(description.source_sensor_key, coordinator.model)
    )


class CtcBinarySensor(CtcEntity, BinarySensorEntity):
    """CTC binary sensor."""

    entity_description: CtcBinarySensorDescription

    def __init__(
        self,
        coordinator: CtcDataUpdateCoordinator,
        description: CtcBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator)


def _bool_from_sensor(coordinator: CtcDataUpdateCoordinator, key: str) -> bool | None:
    """Return a bool from a numeric sensor value."""
    value = coordinator.data.sensors.get(key)
    if value is None:
        return None
    return bool(value)
