# CTC BMS codes

CTC lists BMS codes in a PDF. This script extracts the register tables into CSV files.

## Installation, uv
```bash
uv sync
uv run extract-bms-codes.py
```

The generated files are written to `extracted_tables/`, one CSV per table
schema. The current PDF produces:

- `bms_codes.csv` for the BMS-code list on page 23.
- `modbus_registers.csv` for the shared register table on pages 24–44.

Each register appears once; visual line wraps are joined with spaces in the
original cell, and pages without a recognizable register table are skipped.
