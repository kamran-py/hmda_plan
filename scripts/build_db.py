from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Iterable

import duckdb

from scripts.config import ALL_YEARS, DUCKDB_DIR, PARQUET_DIR, SMOKE_TEST_YEARS, source_era_for_year, year_spec


DATABASE_PATH = DUCKDB_DIR / "hmda_panel.duckdb"
BUILD_LOG_PATH = DUCKDB_DIR / "build_metadata.json"


@dataclass(frozen=True)
class MetadataRow:
    column_name: str
    description: str
    source_era: str
    source_columns: str
    data_type: str
    valid_years: str
    notes: str


CANONICAL_METADATA = [
    MetadataRow(
        "activity_year",
        "HMDA reporting year.",
        "all",
        "activity_year",
        "INTEGER",
        "2007-2024",
        "Already canonical in all converted annual Parquet files.",
    ),
    MetadataRow(
        "source_era",
        "HMDA schema era for the record.",
        "all",
        "source_era",
        "VARCHAR",
        "2007-2024",
        "pre_2018 for 2007-2017 and post_2018 for 2018-2024.",
    ),
    MetadataRow(
        "lender_id",
        "Canonical lender identifier field for within-era analysis.",
        "all",
        "lei_or_respondent_id",
        "VARCHAR",
        "2007-2024",
        "Historic respondent_id and post-2018 LEI are not equivalent ID systems.",
    ),
    MetadataRow(
        "lender_id_type",
        "Identifier system used for lender_id.",
        "all",
        "source_era",
        "VARCHAR",
        "2007-2024",
        "respondent_id for pre_2018 and lei for post_2018.",
    ),
    MetadataRow(
        "state_code",
        "State FIPS code as reported in HMDA.",
        "all",
        "state_code",
        "VARCHAR",
        "2007-2024",
        "Kept as text to preserve leading zeros.",
    ),
    MetadataRow(
        "county_code",
        "County FIPS code as reported in HMDA.",
        "all",
        "county_code",
        "VARCHAR",
        "2007-2024",
        "Kept as text to preserve leading zeros and missing/suppressed values.",
    ),
    MetadataRow(
        "census_tract",
        "Census tract field normalized across HMDA eras.",
        "all",
        "census_tract_number; census_tract",
        "VARCHAR",
        "2007-2024",
        "Uses census_tract_number before 2018 and census_tract from 2018 onward.",
    ),
    MetadataRow(
        "loan_amount",
        "Loan amount normalized to dollars for first-pass analysis.",
        "all",
        "loan_amount_000s; loan_amount",
        "DOUBLE",
        "2007-2024",
        "Historic loan_amount_000s is multiplied by 1000; post-2018 loan_amount is cast directly.",
    ),
    MetadataRow(
        "loan_type",
        "HMDA loan type code.",
        "all",
        "loan_type",
        "VARCHAR",
        "2007-2024",
        "Era-specific code meanings should be documented before final analysis.",
    ),
    MetadataRow(
        "loan_purpose",
        "HMDA loan purpose code.",
        "all",
        "loan_purpose",
        "VARCHAR",
        "2007-2024",
        "Code meanings changed across HMDA eras and need metadata.",
    ),
    MetadataRow(
        "occupancy_type",
        "Occupancy code normalized across eras.",
        "all",
        "owner_occupancy; occupancy_type",
        "VARCHAR",
        "2007-2024",
        "Uses owner_occupancy before 2018 and occupancy_type from 2018 onward.",
    ),
    MetadataRow(
        "action_taken",
        "HMDA action taken code.",
        "all",
        "action_taken",
        "VARCHAR",
        "2007-2024",
        "Aggregation definitions should map codes explicitly.",
    ),
    MetadataRow(
        "applicant_income",
        "Applicant income as reported in HMDA source fields.",
        "all",
        "applicant_income_000s; income",
        "DOUBLE",
        "2007-2024",
        "Units require confirmation before income-level analysis.",
    ),
    MetadataRow(
        "raw_source_columns",
        "Selected source-era raw fields retained for debugging schema differences.",
        "all",
        "as_of_year/respondent_id/loan_amount_000s/owner_occupancy/applicant_income_000s/census_tract_number; raw_activity_year/lei/loan_amount/occupancy_type/income/census_tract",
        "JSON",
        "2007-2024",
        "Stores selected raw values used for canonical mappings, not the full source record.",
    ),
]


def sql_string(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return "'" + text.replace("'", "''") + "'"


def selected_years(args: argparse.Namespace) -> list[int]:
    if args.all_years:
        return list(ALL_YEARS)
    if args.years:
        return args.years
    return list(SMOKE_TEST_YEARS)


def source_select_sql(year: int) -> str:
    spec = year_spec(year)
    path = sql_string(spec.parquet_path)
    era = source_era_for_year(year)
    if era == "pre_2018":
        census_expr = "census_tract_number"
        loan_amount_expr = "TRY_CAST(NULLIF(TRIM(loan_amount_000s), '') AS DOUBLE) * 1000"
        occupancy_expr = "owner_occupancy"
        income_expr = "TRY_CAST(NULLIF(TRIM(applicant_income_000s), '') AS DOUBLE)"
        lender_type = "respondent_id"
        raw_source_expr = """
    json_object(
        'as_of_year', as_of_year,
        'respondent_id', respondent_id,
        'loan_amount_000s', loan_amount_000s,
        'owner_occupancy', owner_occupancy,
        'applicant_income_000s', applicant_income_000s,
        'census_tract_number', census_tract_number
    )
""".strip()
    else:
        census_expr = "census_tract"
        loan_amount_expr = "TRY_CAST(NULLIF(TRIM(loan_amount), '') AS DOUBLE)"
        occupancy_expr = "occupancy_type"
        income_expr = "TRY_CAST(NULLIF(TRIM(income), '') AS DOUBLE)"
        lender_type = "lei"
        raw_source_expr = """
    json_object(
        'raw_activity_year', raw_activity_year,
        'lei', lei,
        'loan_amount', loan_amount,
        'occupancy_type', occupancy_type,
        'income', income,
        'census_tract', census_tract
    )
""".strip()

    return f"""
SELECT
    TRY_CAST(activity_year AS INTEGER) AS activity_year,
    source_era::VARCHAR AS source_era,
    lei_or_respondent_id::VARCHAR AS lender_id,
    '{lender_type}'::VARCHAR AS lender_id_type,
    state_code::VARCHAR AS state_code,
    county_code::VARCHAR AS county_code,
    {census_expr}::VARCHAR AS census_tract,
    {loan_amount_expr} AS loan_amount,
    loan_type::VARCHAR AS loan_type,
    loan_purpose::VARCHAR AS loan_purpose,
    {occupancy_expr}::VARCHAR AS occupancy_type,
    action_taken::VARCHAR AS action_taken,
    {income_expr} AS applicant_income,
    {raw_source_expr} AS raw_source_columns
FROM read_parquet({path})
""".strip()


def loan_years_view_sql(years: Iterable[int]) -> str:
    selects = "\nUNION ALL\n".join(source_select_sql(year) for year in years)
    return f"CREATE OR REPLACE VIEW loan_years AS\n{selects};"


def create_column_metadata(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE column_metadata (
            column_name VARCHAR,
            description VARCHAR,
            source_era VARCHAR,
            source_columns VARCHAR,
            data_type VARCHAR,
            valid_years VARCHAR,
            notes VARCHAR
        );
        """
    )
    con.executemany(
        "INSERT INTO column_metadata VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row.column_name,
                row.description,
                row.source_era,
                row.source_columns,
                row.data_type,
                row.valid_years,
                row.notes,
            )
            for row in CANONICAL_METADATA
        ],
    )


def create_year_summary(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE year_summary AS
        SELECT
            activity_year,
            COUNT(*) AS row_count,
            COUNT(DISTINCT state_code) FILTER (WHERE state_code IS NOT NULL AND TRIM(state_code) <> '') AS state_count,
            COUNT(DISTINCT state_code || '-' || county_code)
                FILTER (WHERE state_code IS NOT NULL AND county_code IS NOT NULL
                        AND TRIM(state_code) <> '' AND TRIM(county_code) <> '') AS county_count,
            COUNT(DISTINCT lender_id)
                FILTER (WHERE lender_id IS NOT NULL AND TRIM(lender_id) <> '') AS lender_count,
            SUM(loan_amount) AS total_loan_amount
        FROM loan_years
        GROUP BY activity_year
        ORDER BY activity_year;
        """
    )


def create_build_log_table(con: duckdb.DuckDBPyConnection, log: dict[str, object]) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE build_log (
            key VARCHAR,
            value VARCHAR
        );
        """
    )
    con.executemany(
        "INSERT INTO build_log VALUES (?, ?)",
        [(key, json.dumps(value) if isinstance(value, (dict, list)) else str(value)) for key, value in log.items()],
    )


def build_database(years: list[int], *, force: bool) -> dict[str, object]:
    DUCKDB_DIR.mkdir(parents=True, exist_ok=True)
    if DATABASE_PATH.exists():
        if force:
            DATABASE_PATH.unlink()
        else:
            raise FileExistsError(f"Database already exists: {DATABASE_PATH}. Pass --force to rebuild.")

    started_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    con = duckdb.connect(str(DATABASE_PATH))
    try:
        con.execute("PRAGMA threads=4")
        con.execute(loan_years_view_sql(years))
        create_column_metadata(con)
        create_year_summary(con)
        summary_rows = con.execute("SELECT COUNT(*), SUM(row_count) FROM year_summary").fetchone()
        finished_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        log = {
            "database_path": str(DATABASE_PATH),
            "started_at": started_at,
            "finished_at": finished_at,
            "years": years,
            "source_parquet_files": [str(year_spec(year).parquet_path) for year in years],
            "objects_created": ["loan_years", "column_metadata", "year_summary", "build_log"],
            "loan_years_kind": "VIEW",
            "year_summary_years": int(summary_rows[0]),
            "year_summary_total_rows": int(summary_rows[1]),
            "notes": [
                "No final research aggregates were created.",
                "Raw files were not deleted.",
                "loan_years is a view over annual Parquet files.",
            ],
        }
        create_build_log_table(con, log)
        BUILD_LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")
        return log
    finally:
        con.close()


def build_database_plan(years: Iterable[int], *, force: bool) -> list[str]:
    year_list = list(years)
    lines = [
        "DuckDB build plan.",
        f"database: {DATABASE_PATH}",
        f"force rebuild: {force}",
        "objects: loan_years view, column_metadata table, year_summary table, build_log table",
        "research aggregates: not created",
    ]
    for year in year_list:
        spec = year_spec(year)
        lines.append(f"{year}: {spec.parquet_path}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the first HMDA DuckDB database from annual Parquet files.")
    parser.add_argument("--years", nargs="*", type=int)
    parser.add_argument("--all-years", action="store_true", help="Use all supported HMDA years, 2007-2024.")
    parser.add_argument("--dry-run", action="store_true", help="Print the build plan without creating a database.")
    parser.add_argument("--force", action="store_true", help="Rebuild the DuckDB database if it already exists.")
    args = parser.parse_args()

    years = selected_years(args)
    if args.dry_run:
        for line in build_database_plan(years, force=args.force):
            print(line)
        return 0

    log = build_database(years, force=args.force)
    print(f"database: {DATABASE_PATH}")
    print(f"build log: {BUILD_LOG_PATH}")
    print(f"years: {log['year_summary_years']}")
    print(f"rows: {log['year_summary_total_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
