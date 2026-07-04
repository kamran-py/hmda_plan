from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Iterable

from scripts.config import ALL_YEARS, PARQUET_DIR, SMOKE_TEST_YEARS, source_era_for_year, year_spec


METADATA_PATH = PARQUET_DIR / "conversion_metadata.json"
TEMP_ROOT = Path("data/raw/.convert_tmp")
CANONICAL_PREFIX_COLUMNS = ("activity_year", "source_era", "lei_or_respondent_id")
GEOGRAPHY_COLUMNS = ("state_code", "county_code")
LENDER_COLUMNS = ("respondent_id", "lei", "lei_or_respondent_id")


@dataclass
class PreparedInput:
    year: int
    source_era: str
    raw_input_path: Path
    readable_csv_path: Path
    parquet_output_path: Path
    input_columns: list[str]
    temp_dir: Path | None = None
    zip_member: str | None = None


@dataclass
class ConversionRecord:
    year: int
    raw_input_path: str
    parquet_output_path: str
    source_era: str
    input_columns: list[str]
    output_columns: list[str]
    row_count: int | None
    conversion_status: str
    error: str | None
    validation: dict[str, object]
    zip_member: str | None = None
    temp_working_path: str | None = None


def build_conversion_plan(years: Iterable[int]) -> list[str]:
    lines = [
        "Conversion plan. Omit --dry-run to write Parquet outputs using DuckDB.",
        "Cached-raw mode reads existing files from data/raw and does not download data.",
    ]
    for year in years:
        spec = year_spec(year)
        lines.append(f"{year} ({spec.source_era})")
        lines.append(f"  input: {spec.raw_path}")
        lines.append(f"  output: {spec.parquet_path}")
    return lines


def selected_years(args: argparse.Namespace) -> list[int]:
    if args.all_years:
        return list(ALL_YEARS)
    if args.years:
        return args.years
    return list(SMOKE_TEST_YEARS)


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return next(csv.reader(handle))


def inspect_zip_csv(path: Path) -> tuple[str, list[str]]:
    with zipfile.ZipFile(path) as archive:
        csv_members = [info for info in archive.infolist() if info.filename.lower().endswith(".csv")]
        if len(csv_members) != 1:
            names = [info.filename for info in archive.infolist()]
            raise ValueError(f"Expected exactly one CSV member in {path}; found {names}")
        member = csv_members[0]
        with archive.open(member, "r") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            header = next(csv.reader(text))
        return member.filename, header


def extract_zip_member_to_temp(zip_path: Path, member_name: str, year: int) -> tuple[Path, Path]:
    temp_dir = TEMP_ROOT / str(year)
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / Path(member_name).name
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member_name, "r") as source, output_path.open("wb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    return temp_dir, output_path


def prepare_input(year: int) -> PreparedInput:
    spec = year_spec(year)
    source_era = source_era_for_year(year)
    if source_era == "pre_2018":
        member_name, input_columns = inspect_zip_csv(spec.raw_path)
        temp_dir, readable_csv_path = extract_zip_member_to_temp(spec.raw_path, member_name, year)
        return PreparedInput(
            year=year,
            source_era=source_era,
            raw_input_path=spec.raw_path,
            readable_csv_path=readable_csv_path,
            parquet_output_path=spec.parquet_path,
            input_columns=input_columns,
            temp_dir=temp_dir,
            zip_member=member_name,
        )

    return PreparedInput(
        year=year,
        source_era=source_era,
        raw_input_path=spec.raw_path,
        readable_csv_path=spec.raw_path,
        parquet_output_path=spec.parquet_path,
        input_columns=read_csv_header(spec.raw_path),
    )


def prepare_existing_output(year: int) -> PreparedInput:
    spec = year_spec(year)
    source_era = source_era_for_year(year)
    if source_era == "pre_2018":
        member_name, input_columns = inspect_zip_csv(spec.raw_path)
        return PreparedInput(
            year=year,
            source_era=source_era,
            raw_input_path=spec.raw_path,
            readable_csv_path=spec.raw_path,
            parquet_output_path=spec.parquet_path,
            input_columns=input_columns,
            zip_member=member_name,
        )

    return PreparedInput(
        year=year,
        source_era=source_era,
        raw_input_path=spec.raw_path,
        readable_csv_path=spec.raw_path,
        parquet_output_path=spec.parquet_path,
        input_columns=read_csv_header(spec.raw_path),
    )


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sql_string(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return "'" + text.replace("'", "''") + "'"


def raw_alias(column: str) -> str:
    return f"raw_{column}" if column in CANONICAL_PREFIX_COLUMNS else column


def select_expressions(prepared: PreparedInput) -> list[str]:
    if prepared.source_era == "pre_2018":
        activity_expr = 'TRY_CAST("as_of_year" AS INTEGER) AS activity_year'
        lender_expr = '"respondent_id" AS lei_or_respondent_id'
    else:
        activity_expr = 'TRY_CAST("activity_year" AS INTEGER) AS activity_year'
        lender_expr = '"lei" AS lei_or_respondent_id'

    expressions = [
        activity_expr,
        f"'{prepared.source_era}' AS source_era",
        lender_expr,
    ]
    for column in prepared.input_columns:
        alias = raw_alias(column)
        expr = quote_identifier(column)
        if alias != column:
            expr += f" AS {quote_identifier(alias)}"
        expressions.append(expr)
    return expressions


def conversion_sql(prepared: PreparedInput) -> str:
    select_sql = ",\n    ".join(select_expressions(prepared))
    return f"""
COPY (
  SELECT
    {select_sql}
  FROM read_csv({sql_string(prepared.readable_csv_path)}, header = true, all_varchar = true)
) TO {sql_string(prepared.parquet_output_path)} (FORMAT PARQUET, COMPRESSION ZSTD);
""".strip()


def output_columns(prepared: PreparedInput) -> list[str]:
    columns = list(CANONICAL_PREFIX_COLUMNS)
    columns.extend(raw_alias(column) for column in prepared.input_columns)
    return columns


def validate_output(con, prepared: PreparedInput, expected_columns: list[str]) -> dict[str, object]:
    parquet_path = sql_string(prepared.parquet_output_path)
    row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet({parquet_path})").fetchone()[0]
    parquet_columns = [row[0] for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet({parquet_path})").fetchall()]
    validation = {
        "row_count_gt_zero": row_count > 0,
        "parquet_exists": prepared.parquet_output_path.exists(),
        "duckdb_query_ok": True,
        "activity_year_present": "activity_year" in parquet_columns,
        "geography_fields": [column for column in GEOGRAPHY_COLUMNS if column in parquet_columns],
        "geography_unmapped": [column for column in GEOGRAPHY_COLUMNS if column not in parquet_columns],
        "lender_identifier_fields": [column for column in LENDER_COLUMNS if column in parquet_columns],
        "lender_identifier_unmapped": not any(column in parquet_columns for column in LENDER_COLUMNS),
        "expected_columns_present": all(column in parquet_columns for column in expected_columns),
    }
    validation["passed"] = all(
        [
            validation["row_count_gt_zero"],
            validation["parquet_exists"],
            validation["duckdb_query_ok"],
            validation["activity_year_present"],
            bool(validation["geography_fields"]),
            not validation["lender_identifier_unmapped"],
        ]
    )
    validation["row_count"] = row_count
    validation["parquet_columns"] = parquet_columns
    return validation


def convert_year(year: int, *, force: bool, keep_temp: bool) -> ConversionRecord:
    try:
        import duckdb
    except ImportError as exc:
        spec = year_spec(year)
        return ConversionRecord(
            year=year,
            raw_input_path=str(spec.raw_path),
            parquet_output_path=str(spec.parquet_path),
            source_era=source_era_for_year(year),
            input_columns=[],
            output_columns=[],
            row_count=None,
            conversion_status="failed",
            error=f"DuckDB Python package is required: {exc}",
            validation={"passed": False, "duckdb_query_ok": False},
        )

    prepared: PreparedInput | None = None
    try:
        spec = year_spec(year)
        if spec.parquet_path.exists():
            existing = validate_existing_year(year)
            if existing.validation.get("passed") and not force:
                existing.conversion_status = "skipped_existing"
                existing.error = None
                return existing
            if force or not existing.validation.get("passed"):
                spec.parquet_path.unlink()

        prepared = prepare_input(year)
        prepared.parquet_output_path.parent.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(database=":memory:")
        con.execute(conversion_sql(prepared))
        expected_columns = output_columns(prepared)
        validation = validate_output(con, prepared, expected_columns)
        row_count = int(validation["row_count"])
        status = "converted" if validation["passed"] else "validation_failed"
        return ConversionRecord(
            year=year,
            raw_input_path=str(prepared.raw_input_path),
            parquet_output_path=str(prepared.parquet_output_path),
            source_era=prepared.source_era,
            input_columns=prepared.input_columns,
            output_columns=validation["parquet_columns"],
            row_count=row_count,
            conversion_status=status,
            error=None if status == "converted" else "Validation failed",
            validation=validation,
            zip_member=prepared.zip_member,
            temp_working_path=str(prepared.temp_dir) if prepared.temp_dir else None,
        )
    except Exception as exc:
        spec = year_spec(year)
        return ConversionRecord(
            year=year,
            raw_input_path=str(prepared.raw_input_path if prepared else spec.raw_path),
            parquet_output_path=str(prepared.parquet_output_path if prepared else spec.parquet_path),
            source_era=prepared.source_era if prepared else source_era_for_year(year),
            input_columns=prepared.input_columns if prepared else [],
            output_columns=[],
            row_count=None,
            conversion_status="failed",
            error=str(exc),
            validation={"passed": False},
            zip_member=prepared.zip_member if prepared else None,
            temp_working_path=str(prepared.temp_dir) if prepared and prepared.temp_dir else None,
        )
    finally:
        if prepared and prepared.temp_dir and not keep_temp:
            shutil.rmtree(prepared.temp_dir, ignore_errors=True)


def write_metadata(records: list[ConversionRecord], path: Path = METADATA_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump([asdict(record) for record in records], handle, indent=2)
        handle.write("\n")


def validate_existing_year(year: int) -> ConversionRecord:
    try:
        import duckdb
    except ImportError as exc:
        spec = year_spec(year)
        return ConversionRecord(
            year=year,
            raw_input_path=str(spec.raw_path),
            parquet_output_path=str(spec.parquet_path),
            source_era=source_era_for_year(year),
            input_columns=[],
            output_columns=[],
            row_count=None,
            conversion_status="failed",
            error=f"DuckDB Python package is required: {exc}",
            validation={"passed": False, "duckdb_query_ok": False},
        )

    try:
        prepared = prepare_existing_output(year)
        con = duckdb.connect(database=":memory:")
        expected_columns = output_columns(prepared)
        validation = validate_output(con, prepared, expected_columns)
        status = "converted" if validation["passed"] else "validation_failed"
        return ConversionRecord(
            year=year,
            raw_input_path=str(prepared.raw_input_path),
            parquet_output_path=str(prepared.parquet_output_path),
            source_era=prepared.source_era,
            input_columns=prepared.input_columns,
            output_columns=validation["parquet_columns"],
            row_count=int(validation["row_count"]),
            conversion_status=status,
            error=None if status == "converted" else "Validation failed",
            validation=validation,
            zip_member=prepared.zip_member,
            temp_working_path=None,
        )
    except Exception as exc:
        spec = year_spec(year)
        return ConversionRecord(
            year=year,
            raw_input_path=str(spec.raw_path),
            parquet_output_path=str(spec.parquet_path),
            source_era=source_era_for_year(year),
            input_columns=[],
            output_columns=[],
            row_count=None,
            conversion_status="failed",
            error=str(exc),
            validation={"passed": False},
        )


def validate_existing_outputs(years: Iterable[int]) -> int:
    records: list[ConversionRecord] = []
    exit_code = 0
    for year in years:
        print(f"{year}: validating existing Parquet output")
        record = validate_existing_year(year)
        records.append(record)
        print(f"{year}: {record.conversion_status}")
        if record.error:
            print(f"{year}: error: {record.error}")
            exit_code = 1
    write_metadata(records)
    print(f"conversion metadata: {METADATA_PATH}")
    return exit_code


def run_conversion(years: Iterable[int], *, force: bool, keep_temp: bool) -> int:
    records: list[ConversionRecord] = []
    exit_code = 0
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    for year in years:
        print(f"{year}: converting cached raw input")
        record = convert_year(year, force=force, keep_temp=keep_temp)
        records.append(record)
        write_metadata(records)
        print(f"{year}: {record.conversion_status}")
        if record.error:
            print(f"{year}: error: {record.error}")
            print(f"Stopping after failure in {year}.")
            print(f"conversion metadata: {METADATA_PATH}")
            return 1
    print(f"conversion metadata: {METADATA_PATH}")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert cached HMDA raw files to Parquet using DuckDB.")
    parser.add_argument("--years", nargs="*", type=int, default=list(SMOKE_TEST_YEARS))
    parser.add_argument("--all-years", action="store_true", help="Use all supported HMDA years, 2007-2024.")
    parser.add_argument("--dry-run", action="store_true", help="Print the conversion plan without writing Parquet.")
    parser.add_argument("--validate-existing", action="store_true", help="Validate existing Parquet outputs and refresh metadata.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Parquet outputs.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary extracted CSV files.")
    args = parser.parse_args()

    years = selected_years(args)
    if args.dry_run:
        for line in build_conversion_plan(years):
            print(line)
        print("Omit --dry-run to run conversion after approval.")
        return 0

    if args.validate_existing:
        return validate_existing_outputs(years)

    return run_conversion(years, force=args.force, keep_temp=args.keep_temp)


if __name__ == "__main__":
    raise SystemExit(main())
