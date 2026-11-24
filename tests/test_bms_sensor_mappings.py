"""Tests for sensor mappings verified against the CTC BMS register table."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    """Load a standalone integration module without Home Assistant installed."""
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


registers = load_module(
    "_ctc_test_registers",
    "custom_components/ctc_heat_pump/registers.py",
)
status = load_module(
    "_ctc_test_status",
    "custom_components/ctc_heat_pump/status.py",
)


class BmsSensorMappingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sensors = {sensor.key: sensor for sensor in registers.SENSOR_REGISTERS}

    def test_corrected_register_codes_and_decoding(self) -> None:
        self.assertEqual(self.sensors["heat_pump_status"].address, 62017)
        self.assertEqual(
            self.sensors["heat_pump_status"].data_type,
            registers.RegisterType.INT16,
        )

        lower_temp = self.sensors["dhw_bottom_temperature"]
        self.assertEqual(lower_temp.address, 62275)
        self.assertEqual(lower_temp.data_type, registers.RegisterType.INT16)
        self.assertEqual(lower_temp.scale, 0.1)

        setpoint = self.sensors["dhw_setpoint_float"]
        self.assertEqual(setpoint.address, 62002)
        self.assertEqual(setpoint.data_type, registers.RegisterType.INT16)

        top_temp = self.sensors["dhw_tank_top_temperature"]
        self.assertEqual(top_temp.address, 62363)
        self.assertEqual(top_temp.data_type, registers.RegisterType.UINT16)

        periodic_dhw = self.sensors["periodic_extra_dhw_status"]
        self.assertEqual(periodic_dhw.address, 62365)
        self.assertEqual(periodic_dhw.data_type, registers.RegisterType.UINT16)
        self.assertFalse(periodic_dhw.enabled_default)

    def test_unmatched_sensors_remain_disabled(self) -> None:
        unmatched_keys = (
            "cop_heating",
            "cop_hot_water",
            "cop_total",
            "info_code",
            "dhw_diff",
        )
        for key in unmatched_keys:
            with self.subTest(key=key):
                self.assertFalse(self.sensors[key].enabled_default)

    def test_documented_status_values_are_interpreted_exactly(self) -> None:
        self.assertEqual(status.HEAT_PUMP_STATUS_DHW_CHARGING, 33)
        self.assertEqual(status.PERIODIC_EXTRA_DHW_UNDEFINED, 0)
        self.assertEqual(status.PERIODIC_EXTRA_DHW_ACTIVE, 1)

        self.assertIs(
            status.is_dhw_charge_active(status.HEAT_PUMP_STATUS_DHW_CHARGING),
            True,
        )
        self.assertIs(status.is_dhw_charge_active(32), False)
        self.assertIs(status.is_dhw_charge_active(None), None)

        self.assertIs(
            status.is_periodic_extra_dhw_active(status.PERIODIC_EXTRA_DHW_ACTIVE),
            True,
        )
        self.assertIs(status.is_periodic_extra_dhw_active(2), False)
        self.assertIs(
            status.is_periodic_extra_dhw_active(status.PERIODIC_EXTRA_DHW_UNDEFINED),
            None,
        )
        self.assertIs(status.is_periodic_extra_dhw_active(None), None)


if __name__ == "__main__":
    unittest.main()
