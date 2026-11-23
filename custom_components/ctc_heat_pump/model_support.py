"""Model compatibility for curated CTC BMS register definitions.

The BMS PDF contains many more codes than the integration should expose. Keep
compatibility here limited to codes that the integration actually defines in
``registers.py``. Unverified legacy model behavior remains unchanged; GSi
registers are exposed only when the BMS CSV confirms their address.
"""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry

from .const import CONF_MODEL, DEFAULT_MODEL

# Register key -> model identifiers verified to implement that code.
# Use a frozenset so the compatibility data is immutable at runtime. Add keys
# only for curated integration registers; do not import the entire PDF table.
REGISTER_COMPATIBILITY: dict[str, frozenset[str]] = {
    "outdoor_temperature": frozenset({"gsi_ctc_gs"}),
    "dhw_manual_stop_temperature": frozenset({"gsi_ctc_gs"}),
    "dhw_setpoint": frozenset({"gsi_ctc_gs"}),
    "hot_water_temperature": frozenset({"gsi_ctc_gs"}),
    "dhw_upper_temperature": frozenset({"gsi_ctc_gs"}),
    "dhw_capacity": frozenset({"gsi_ctc_gs"}),
    "dhw_stop_temperature_control": frozenset({"gsi_ctc_gs"}),
    "hc1_supply_temperature": frozenset({"gsi_ctc_gs"}),
    "return_temperature": frozenset({"gsi_ctc_gs"}),
    "brine_in_temperature": frozenset({"gsi_ctc_gs"}),
    "brine_out_temperature": frozenset({"gsi_ctc_gs"}),
    "hp1_power_consumption": frozenset({"gsi_ctc_gs"}),
    "immersion_heater_power": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_1_outdoor": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_1_supply": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_2_outdoor": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_2_supply": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_3_outdoor": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_3_supply": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_4_outdoor": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_4_supply": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_5_outdoor": frozenset({"gsi_ctc_gs"}),
    "hc1_curve_point_5_supply": frozenset({"gsi_ctc_gs"}),
}
# Curated register keys whose BMS addresses are marked as supported for
# GSi / CTC GS in the extracted BMS CSV tables.
GSI_COMPATIBLE_REGISTERS = frozenset(
    {
        "lower_heater_feedback",          # 61590
        "upper_heater_feedback",          # 61591
        "outdoor_temperature",            # 62000
        "dhw_stop_temperature",           # 62001
        "hot_water_temperature",          # 62003
        "system_status",                  # 62005
        "dhw_setpoint",                   # 61502
        "dhw_minimum_temperature",        # 61503
        "dhw_comfort_boost",              # 61506
        "room_temp_setpoint_hc1",         # 61509
        "heating_curve_slope_hc1",        # 61513
        "max_lower_heater_power",         # 61590
        "max_upper_heater_power",         # 61591
        "smartgrid_mode",                 # 1100
    }
)

# Register key -> model identifiers verified to implement that code.
# Use a frozenset so the compatibility data is immutable at runtime.
REGISTER_COMPATIBILITY: dict[str, frozenset[str]] = {}


def selected_model(entry: ConfigEntry) -> str:
    """Return the model selected in options, falling back to setup data."""
    return entry.options.get(
        CONF_MODEL,
        entry.data.get(CONF_MODEL, DEFAULT_MODEL),
    )


def is_compatible(register_key: str, model: str) -> bool:
    """Return whether a curated code is available for the selected model."""
    compatible_models = REGISTER_COMPATIBILITY.get(register_key)
    if compatible_models is not None:
        return model in compatible_models

    if model == "gsi_ctc_gs":
        return register_key in GSI_COMPATIBLE_REGISTERS

    # Keep the existing behavior for models whose compatibility has not been
    # explicitly checked.
    return True


def compatible_registers(registers: Iterable, model: str) -> tuple:
    """Filter register definitions to those available for one model."""
    return tuple(
        register
        for register in registers
        if is_compatible(register.key, model)
    )

