from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COUNTY_CSV_PATH = PROJECT_ROOT / "output" / "county_year_lending.csv"
LENDER_SAMPLE_CSV_PATH = PROJECT_ROOT / "output" / "lender_county_year_sample.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "committed_output_profile.md"


def fmt_int(value: Any) -> str:
    return f"{int(value):,}"


def fmt_float(value: float) -> str:
    return f"{value:.3f}"


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def read_county_profile() -> dict[str, Any]:
    by_year: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "county_count": 0,
            "total_records": 0,
            "originated_loans": 0,
            "denied_applications": 0,
            "total_loan_amount": 0.0,
            "lender_counts": [],
        }
    )
    largest_county_years: list[tuple[int, int, str, int, int, int]] = []
    largest_lender_counts: list[tuple[int, int, str, int]] = []

    with COUNTY_CSV_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            year = int(row["activity_year"])
            total_records = int(row.get("total_records") or row["total_applications"])
            originated_loans = int(row["originated_loans"])
            denied_applications = int(row["denied_applications"])
            total_loan_amount = float(row["total_loan_amount"] or 0)
            lender_count = int(row["lender_count"])

            bucket = by_year[year]
            bucket["county_count"] += 1
            bucket["total_records"] += total_records
            bucket["originated_loans"] += originated_loans
            bucket["denied_applications"] += denied_applications
            bucket["total_loan_amount"] += total_loan_amount
            bucket["lender_counts"].append(lender_count)

            largest_county_years.append(
                (total_records, year, row["county_fips_5"], originated_loans, denied_applications, lender_count)
            )
            largest_lender_counts.append((lender_count, year, row["county_fips_5"], total_records))

    year_rows: list[dict[str, Any]] = []
    for year in sorted(by_year):
        bucket = by_year[year]
        total_records = bucket["total_records"]
        originated_loans = bucket["originated_loans"]
        denied_applications = bucket["denied_applications"]
        other_records = total_records - originated_loans - denied_applications
        lender_counts = sorted(bucket["lender_counts"])
        median_lender_count = lender_counts[len(lender_counts) // 2]
        year_rows.append(
            {
                "activity_year": year,
                "county_count": fmt_int(bucket["county_count"]),
                "total_records": fmt_int(total_records),
                "origination_share": fmt_float(originated_loans / total_records),
                "denial_share": fmt_float(denied_applications / total_records),
                "other_action_share": fmt_float(other_records / total_records),
                "average_record_amount": fmt_int(bucket["total_loan_amount"] / total_records),
                "median_lender_count": fmt_int(median_lender_count),
            }
        )

    top_records = [
        {
            "activity_year": year,
            "county_fips_5": county_fips_5,
            "total_records": fmt_int(total_records),
            "originated_loans": fmt_int(originated_loans),
            "denied_applications": fmt_int(denied_applications),
            "lender_count": fmt_int(lender_count),
        }
        for total_records, year, county_fips_5, originated_loans, denied_applications, lender_count in sorted(
            largest_county_years, reverse=True
        )[:10]
    ]
    top_lender_counts = [
        {
            "activity_year": year,
            "county_fips_5": county_fips_5,
            "lender_count": fmt_int(lender_count),
            "total_records": fmt_int(total_records),
        }
        for lender_count, year, county_fips_5, total_records in sorted(largest_lender_counts, reverse=True)[:10]
    ]
    return {
        "year_rows": year_rows,
        "top_records": top_records,
        "top_lender_counts": top_lender_counts,
    }


def read_sample_profile() -> list[dict[str, Any]]:
    by_year: dict[int, int] = defaultdict(int)
    with LENDER_SAMPLE_CSV_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_year[int(row["activity_year"])] += 1
    return [{"activity_year": year, "sample_rows": fmt_int(by_year[year])} for year in sorted(by_year)]


def build_markdown() -> str:
    county_profile = read_county_profile()
    sample_profile = read_sample_profile()
    lines = [
        "# Committed Output Profile",
        "",
        "## Scope",
        "",
        "This profile is computed only from committed CSV outputs. It does not require raw HMDA files, annual Parquet files, the generated DuckDB database, or the full lender-county-year Parquet export.",
        "",
        "The committed `county_year_lending.csv` now separates `total_records`, `application_records`, and `purchased_loans`. The older `total_applications` column is retained as a legacy alias for `total_records`.",
        "",
        "## County-Year Profile",
        "",
        markdown_table(
            county_profile["year_rows"],
            [
                "activity_year",
                "county_count",
                "total_records",
                "origination_share",
                "denial_share",
                "other_action_share",
                "average_record_amount",
                "median_lender_count",
            ],
        ),
        "",
        "## Largest County-Year Cells",
        "",
        markdown_table(
            county_profile["top_records"],
            [
                "activity_year",
                "county_fips_5",
                "total_records",
                "originated_loans",
                "denied_applications",
                "lender_count",
            ],
        ),
        "",
        "## Largest County-Year Lender Counts",
        "",
        markdown_table(
            county_profile["top_lender_counts"],
            ["activity_year", "county_fips_5", "lender_count", "total_records"],
        ),
        "",
        "## Lender Sample Coverage",
        "",
        markdown_table(sample_profile, ["activity_year", "sample_rows"]),
        "",
        "The committed lender-county-year sample is stratified by `activity_year` so the public sample is not limited to the first year in sort order.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    DOC_PATH.write_text(build_markdown(), encoding="utf-8")
    print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
