import csv
import hashlib
import re
from pathlib import Path

import camelot

PDF_PATH = Path("Manual-BMS Manual-16260016-2.pdf")
OUTPUT_DIR = Path("extracted_tables")
REGISTER_PATTERN = re.compile(r"\d+")
KNOWN_HEADERS = {
    "BMS Register",
    "Function",
    "Signed",
    "Read/Write",
    "Max",
    "Min",
    "Step",
    "Visible",
    "Bit",
    "Factor",
    "Name",
    "Description",
    "RW",
    "EcoHeat 400",
    "EcoZenith i250",
    "Gsi/CTC GS",
    "Gsi/GS",
    "EcoVent i350F",
    "EcoZenith i350/",
    "EcoZenith i550",
    "Eco Part6xx M Pro",
    "EcoLogic",
    "EcoLogic M L",
    "Ecologic S",
}


def clean_cell(value):
    """Normalize visual line wraps without discarding any cell text."""
    return " ".join(str(value).split())


def find_header_row(rows):
    for index, row in enumerate(rows):
        if not row or row[0] != "BMS Register":
            continue
        if any(value == "Function" or value.startswith("English") for value in row[1:]):
            return index
    return None


def merge_continuation_rows(rows, width):
    """Join Camelot's physical continuation rows to their register record."""
    records = []
    current = None

    for row in rows:
        cells = (row + [""] * width)[:width]
        if not any(cells):
            continue

        register = cells[0]
        if register:
            if not REGISTER_PATTERN.fullmatch(register):
                raise ValueError(f"Unexpected register value {register!r}")
            if current is not None:
                records.append(current)
            current = cells
            continue

        if current is None:
            raise ValueError("Found a continuation row before the first register")

        for column, value in enumerate(cells):
            if not value:
                continue
            if not current[column]:
                current[column] = value
            elif current[column] != value:
                current[column] = f"{current[column]} {value}"

    if current is not None:
        records.append(current)
    return records


def extract_table(df):
    """Extract a table that has a recognizable BMS register header."""
    if df.empty:
        return None

    rows = [[clean_cell(value) for value in row] for row in df.values.tolist()]
    header_index = find_header_row(rows)
    if header_index is None:
        return None

    headers = rows[header_index]
    data = rows[header_index + 1 :]

    for column in range(len(headers) - 1):
        if (
            not headers[column]
            and any(row[column] for row in data)
            and headers[column + 1]
            and not any(row[column + 1] for row in data)
        ):
            headers[column] = headers[column + 1]
            headers[column + 1] = ""

    keep_columns = [
        column
        for column, header in enumerate(headers)
        if header or any(row[column] for row in data)
    ]
    if any(not headers[column] for column in keep_columns):
        raise ValueError("Found a populated column without a header")

    headers = [headers[column] for column in keep_columns]
    data = [[row[column] for column in keep_columns] for row in data]

    if len(headers) < 2 or headers[0] != "BMS Register":
        raise ValueError("The table header does not include a BMS register column")

    records = merge_continuation_rows(data, len(headers))
    return headers, records


def header_score(headers, records):
    known = sum(header in KNOWN_HEADERS for header in headers)
    populated = sum(bool(header) for header in headers)
    return known, populated, len(records)


def schema_filename(headers):
    if headers[0] == "BMS Register" and headers[1].startswith("English"):
        return "bms_codes.csv"
    if headers[0] == "BMS Register" and headers[1] == "Function":
        return "modbus_registers.csv"

    schema = "\0".join(headers)
    digest = hashlib.sha256(schema.encode("utf-8")).hexdigest()[:8]
    return f"schema_{digest}.csv"


def get_tables():
    # Page 23 has a clean stream layout; later pages need Camelot's hybrid
    # parser to keep the repeated column headers and split text in their cells.
    tables = list(camelot.read_pdf(str(PDF_PATH), pages="23", flavor="stream"))
    tables.extend(camelot.read_pdf(str(PDF_PATH), pages="24-45", flavor="hybrid"))
    return tables


def split_merged_model_columns(table):
    rows = [[clean_cell(value) for value in row] for row in table.df.values.tolist()]
    header_index = find_header_row(rows)
    if header_index is None:
        return table

    merged_index = next(
        (
            index
            for index, value in enumerate(rows[header_index])
            if "EcoVent i350F" in value and "EcoZenith i350/" in value
        ),
        None,
    )
    if merged_index is None:
        return table

    left, right = table.cols[merged_index]
    boundaries = [column[1] for column in table.cols[:-1]]
    boundaries.append((left + right) / 2)
    boundaries.sort()
    refined = camelot.read_pdf(
        str(PDF_PATH),
        pages=str(table.page),
        flavor="hybrid",
        columns=[",".join(str(boundary) for boundary in boundaries)],
    )
    candidates = []
    for candidate in refined:
        extracted = extract_table(candidate.df)
        if extracted is not None:
            headers, records = extracted
            candidates.append(
                (header_score(headers, records), candidate.order, candidate)
            )
    if not candidates:
        raise ValueError("Could not separate the merged product columns")
    return max(candidates, key=lambda item: item[0])[2]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    candidates = {}
    for table in get_tables():
        try:
            extracted = extract_table(table.df)
        except ValueError as error:
            print(f"Skipping page {table.page}, table {table.order}: {error}")
            continue

        if extracted is None:
            print(f"Skipping page {table.page}, table {table.order}: no BMS register header")
            continue

        headers, records = extracted
        candidates.setdefault(table.page, []).append(
            (header_score(headers, records), table.order, headers, records, table)
        )

    schemas = {}
    for page, page_candidates in sorted(candidates.items()):
        _, _, headers, records, table = max(page_candidates, key=lambda item: item[0])
        if any(
            "EcoVent i350F" in header and "EcoZenith i350/" in header
            for header in headers
        ):
            table = split_merged_model_columns(table)
            headers, records = extract_table(table.df)

        schema = tuple(headers)
        if schema not in schemas:
            schemas[schema] = {
                "filename": schema_filename(headers),
                "pages": [],
                "records": [],
            }
        schemas[schema]["pages"].append(page)
        schemas[schema]["records"].extend(records)

    expected_outputs = set()
    for schema, schema_data in schemas.items():
        output_path = OUTPUT_DIR / schema_data["filename"]
        expected_outputs.add(output_path)
        with output_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(schema)
            writer.writerows(schema_data["records"])

        pages = ", ".join(str(page) for page in schema_data["pages"])
        print(
            f"Saved {output_path} ({len(schema_data['records'])} register rows "
            f"from pages {pages})"
        )

    for old_output in OUTPUT_DIR.glob("page_*_table_*.csv"):
        if old_output not in expected_outputs:
            old_output.unlink()
    for old_output in OUTPUT_DIR.glob("schema_*.csv"):
        if old_output not in expected_outputs:
            old_output.unlink()
    for filename in ("bms_codes.csv", "modbus_registers.csv"):
        old_output = OUTPUT_DIR / filename
        if old_output.exists() and old_output not in expected_outputs:
            old_output.unlink()


if __name__ == "__main__":
    main()
