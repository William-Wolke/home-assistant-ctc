import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("extract-bms-codes.py")
SPEC = importlib.util.spec_from_file_location("extract_bms_codes", MODULE_PATH)
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)


class ExtractTableTests(unittest.TestCase):
    def test_normalizes_visual_line_wraps_to_spaces(self):
        self.assertEqual(
            extractor.clean_cell("two wrapped\nlines"),
            "two wrapped lines",
        )

    def test_merges_wrapped_cells_into_the_register_record(self):
        rows = [
            ["1001", "Heating system 1", "", "x"],
            ["", "primary flow", "1", ""],
            ["", "temperature", "", ""],
            ["1002", "Return temperature", "1", "x"],
        ]

        self.assertEqual(
            extractor.merge_continuation_rows(rows, 4),
            [
                ["1001", "Heating system 1 primary flow temperature", "1", "x"],
                ["1002", "Return temperature", "1", "x"],
            ],
        )

    def test_rejects_continuation_without_a_register(self):
        with self.assertRaisesRegex(ValueError, "before the first register"):
            extractor.merge_continuation_rows([["", "orphaned text"]], 2)

    def test_extracts_rows_after_a_repeated_header(self):
        import pandas as pd

        df = pd.DataFrame(
            [
                ["BMS Register", "Function", "Read/Write"],
                ["1001", "Heating system 1", ""],
                ["", "primary flow", "R"],
            ]
        )

        self.assertEqual(
            extractor.extract_table(df),
            (
                ["BMS Register", "Function", "Read/Write"],
                [["1001", "Heating system 1 primary flow", "R"]],
            ),
        )

    def test_moves_header_over_a_blank_column_when_values_are_shifted(self):
        import pandas as pd

        df = pd.DataFrame(
            [
                ["BMS Register", "Function", "", "Name", "EcoLogic M L"],
                ["1001", "Pump status", "pumpStatus", "", "x"],
            ]
        )

        self.assertEqual(
            extractor.extract_table(df),
            (
                ["BMS Register", "Function", "Name", "EcoLogic M L"],
                [["1001", "Pump status", "pumpStatus", "x"]],
            ),
        )


if __name__ == "__main__":
    unittest.main()
