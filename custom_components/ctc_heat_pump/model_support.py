"""Model compatibility for curated CTC BMS register definitions.

The integration's existing sensor, control, and SmartGrid definitions target
the EcoHeat/EcoZenith/EcoVent/EcoLogic product families. Keep the compatibility
list limited to those curated codes; new model-specific codes should be added
to ``registers.py`` and assigned their verified model set here.
"""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry

from .const import CONF_MODEL, DEFAULT_MODEL
from .registers import NUMBER_REGISTERS, SENSOR_REGISTERS, SMARTGRID_REGISTER

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
# Model identifiers whose BMS code families the existing curated definitions
# were written for. GSi / CTC GS and Other are deliberately not included: codes
# for those models should be enabled only after their compatibility is checked.
ECO_SERIES_MODELS = frozenset(
    {
        "ecoheat_400",
        "ecozenith_i250",
        "ecovent_i350f",
        "ecozenith_i350",
        "ecozenith_i550",
        "ecologic",
        "ecologic_s",
    }
)

# Register key -> model identifiers verified to implement that code. Generate
# entries for every curated sensor and number so adding a register cannot
# accidentally leave it with implicit compatibility. SmartGrid is also a
# curated register-backed entity, despite not using a SensorRegister dataclass.
REGISTER_COMPATIBILITY: dict[str, frozenset[str]] = {
    register.key: ECO_SERIES_MODELS
    for register in (*SENSOR_REGISTERS, *NUMBER_REGISTERS)
}
REGISTER_COMPATIBILITY["smartgrid_mode"] = ECO_SERIES_MODELS


def selected_model(entry: ConfigEntry) -> str:
    """Return the model selected in options, falling back to setup data."""
    return entry.options.get(
        CONF_MODEL,
        entry.data.get(CONF_MODEL, DEFAULT_MODEL),
    )


def is_compatible(register_key: str, model: str) -> bool:
    """Return whether a curated code is available for the selected model.

    An omitted key retains the legacy shared-register behavior, which is useful
    for non-register entities. Register definitions are all explicitly listed
    in ``REGISTER_COMPATIBILITY`` above.
    """
    compatible_models = REGISTER_COMPATIBILITY.get(register_key)
    return compatible_models is None or model in compatible_models


def compatible_registers(registers: Iterable, model: str) -> tuple:
    """Filter register definitions to those available for one model."""
    return tuple(
        register
        for register in registers
        if is_compatible(register.key, model)
    )

