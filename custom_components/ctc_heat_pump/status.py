"""Helpers for interpreting CTC status registers."""

from __future__ import annotations

HEAT_PUMP_STATUS_DHW_CHARGING = 33
PERIODIC_EXTRA_DHW_UNDEFINED = 0
PERIODIC_EXTRA_DHW_ACTIVE = 1


def is_dhw_charge_active(value: int | float | None) -> bool | None:
    """Return whether the heat-pump status indicates DHW charging."""
    if value is None:
        return None
    return value == HEAT_PUMP_STATUS_DHW_CHARGING


def is_periodic_extra_dhw_active(value: int | float | None) -> bool | None:
    """Return whether periodic extra DHW is active."""
    if value is None or value == PERIODIC_EXTRA_DHW_UNDEFINED:
        return None
    return value == PERIODIC_EXTRA_DHW_ACTIVE
