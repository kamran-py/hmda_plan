from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hmda_panel.duckdb"
DOC_PATH = PROJECT_ROOT / "docs" / "lender_county_year.md"


LENDER_COUNTY_YEAR_SQL = """
CREATE OR REPLACE TABLE lender_county_year AS
SELECT
    activity_year,
    state_fips_2,
    county_fips_5,
    lender_id,
    ANY_VALUE(lender_id_type) AS lender_id_type,
    COUNT(*) AS applications,
    SUM(CASE WHEN TRIM(action_taken) = '1' THEN 1 ELSE 0 END) AS originated_loans,
    SUM(CASE WHEN TRIM(action_taken) = '3' THEN 1 ELSE 0 END) AS denied_applications,
    SUM(loan_amount) AS total_loan_amount,
    AVG(loan_amount) AS average_loan_amount,
    MEDIAN(loan_amount) AS median_loan_amount,
    SUM(CASE WHEN TRIM(loan_type) = '1' THEN 1 ELSE 0 END) AS loan_type_1_count,
    SUM(CASE WHEN TRIM(loan_type) = '2' THEN 1 ELSE 0 END) AS loan_type_2_count,
    SUM(CASE WHEN TRIM(loan_type) = '3' THEN 1 ELSE 0 END) AS loan_type_3_count,
    SUM(CASE WHEN TRIM(loan_type) = '4' THEN 1 ELSE 0 END) AS loan_type_4_count,
    SUM(
        CASE
            WHEN loan_type IS NULL
              OR TRIM(loan_type) NOT IN ('1', '2', '3', '4')
            THEN 1
            ELSE 0
        END
    ) AS loan_type_other_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '1' THEN 1 ELSE 0 END) AS loan_purpose_1_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '2' THEN 1 ELSE 0 END) AS loan_purpose_2_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '3' THEN 1 ELSE 0 END) AS loan_purpose_3_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '31' THEN 1 ELSE 0 END) AS loan_purpose_31_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '32' THEN 1 ELSE 0 END) AS loan_purpose_32_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '4' THEN 1 ELSE 0 END) AS loan_purpose_4_count,
    SUM(CASE WHEN TRIM(loan_purpose) = '5' THEN 1 ELSE 0 END) AS loan_purpose_5_count,
    SUM(
        CASE
            WHEN loan_purpose IS NULL
              OR TRIM(loan_purpose) NOT IN ('1', '2', '3', '31', '32', '4', '5')
            THEN 1
            ELSE 0
        END
    ) AS loan_purpose_other_count
FROM loan_years_geo
WHERE county_fips_5 IS NOT NULL
  AND lender_id IS NOT NULL
  AND TRIM(lender_id) <> ''
GROUP BY activity_year, state_fips_2, county_fips_5, lender_id
ORDER BY activity_year, state_fips_2, county_fips_5, lender_id;
""".strip()


MISSING_LENDER_SQL = """
CREATE OR REPLACE TABLE lender_county_year_missing_lender_qa AS
SELECT
    activity_year,
    state_fips_2,
    county_fips_5,
    COUNT(*) AS missing_lender_rows,
    SUM(CASE WHEN TRIM(action_taken) = '1' THEN 1 ELSE 0 END) AS originated_loans,
    SUM(CASE WHEN TRIM(action_taken) = '3' THEN 1 ELSE 0 END) AS denied_applications,
    SUM(loan_amount) AS total_loan_amount
FROM loan_years_geo
WHERE county_fips_5 IS NOT NULL
  AND (lender_id IS NULL OR TRIM(lender_id) = '')
GROUP BY activity_year, state_fips_2, county_fips_5
ORDER BY activity_year, state_fips_2, county_fips_5;
""".strip()


MISSING_GEO_SQL = """
CREATE OR REPLACE TABLE lender_county_year_missing_geo_qa AS
SELECT
    activity_year,
    COUNT(*) AS missing_geo_rows,
    SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS missing_state_fips_2,
    SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS missing_county_fips_5,
    SUM(CASE WHEN lender_id IS NULL OR TRIM(lender_id) = '' THEN 1 ELSE 0 END) AS missing_lender_id,
    COUNT(DISTINCT lender_id)
        FILTER (WHERE lender_id IS NOT NULL AND TRIM(lender_id) <> '') AS distinct_lenders,
    SUM(CASE WHEN TRIM(action_taken) = '1' THEN 1 ELSE 0 END) AS originated_loans,
    SUM(CASE WHEN TRIM(action_taken) = '3' THEN 1 ELSE 0 END) AS denied_applications,
    SUM(loan_amount) AS total_loan_amount
FROM loan_years_geo
WHERE county_fips_5 IS NULL
GROUP BY activity_year
ORDER BY activity_year;
""".strip()


def query_dicts(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    result = con.execute(sql)
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def fmt_int(value: Any) -> str:
    if value is None:
        return ""
    return f"{int(value):,}"


def fmt_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):,.0f}"


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def format_int_columns(rows: list[dict[str, Any]], columns: list[str]) -> None:
    for row in rows:
        for column in columns:
            row[column] = fmt_int(row.get(column))


def format_float_columns(rows: list[dict[str, Any]], columns: list[str]) -> None:
    for row in rows:
        for column in columns:
            row[column] = fmt_float(row.get(column))


def build_aggregate() -> dict[str, Any]:
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute(LENDER_COUNTY_YEAR_SQL)
        con.execute(MISSING_LENDER_SQL)
        con.execute(MISSING_GEO_SQL)

        objects = query_dicts(
            con,
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name IN (
                'lender_county_year',
                'lender_county_year_missing_lender_qa',
                'lender_county_year_missing_geo_qa'
              )
            ORDER BY table_name;
            """,
        )
        summary = query_dicts(
            con,
            """
            SELECT
                COUNT(*) AS row_count,
                MIN(activity_year) AS min_year,
                MAX(activity_year) AS max_year,
                SUM(applications) AS applications,
                SUM(originated_loans) AS originated_loans,
                SUM(denied_applications) AS denied_applications,
                SUM(total_loan_amount) AS total_loan_amount
            FROM lender_county_year;
            """,
        )[0]
        by_year = query_dicts(
            con,
            """
            SELECT
                activity_year,
                COUNT(*) AS lender_county_rows,
                COUNT(DISTINCT county_fips_5) AS county_count,
                COUNT(DISTINCT lender_id) AS lender_count,
                SUM(applications) AS applications,
                SUM(originated_loans) AS originated_loans,
                SUM(denied_applications) AS denied_applications,
                SUM(total_loan_amount) AS total_loan_amount
            FROM lender_county_year
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        key_checks = query_dicts(
            con,
            """
            SELECT
                SUM(CASE WHEN activity_year IS NULL THEN 1 ELSE 0 END) AS null_activity_year,
                SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS null_state_fips_2,
                SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS null_county_fips_5,
                SUM(CASE WHEN lender_id IS NULL OR TRIM(lender_id) = '' THEN 1 ELSE 0 END) AS null_or_blank_lender_id
            FROM lender_county_year;
            """,
        )[0]
        duplicate_check = query_dicts(
            con,
            """
            SELECT COUNT(*) AS duplicate_grain_rows
            FROM (
                SELECT activity_year, state_fips_2, county_fips_5, lender_id, COUNT(*) AS row_count
                FROM lender_county_year
                GROUP BY activity_year, state_fips_2, county_fips_5, lender_id
                HAVING COUNT(*) > 1
            );
            """,
        )[0]
        reconciliation = query_dicts(
            con,
            """
            WITH source AS (
                SELECT
                    activity_year,
                    SUM(
                        CASE
                            WHEN county_fips_5 IS NOT NULL
                             AND lender_id IS NOT NULL
                             AND TRIM(lender_id) <> ''
                            THEN 1
                            ELSE 0
                        END
                    ) AS expected_main_rows,
                    SUM(
                        CASE
                            WHEN county_fips_5 IS NOT NULL
                             AND (lender_id IS NULL OR TRIM(lender_id) = '')
                            THEN 1
                            ELSE 0
                        END
                    ) AS expected_missing_lender_rows,
                    SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS expected_missing_geo_rows
                FROM loan_years_geo
                GROUP BY activity_year
            ),
            main AS (
                SELECT activity_year, SUM(applications) AS main_applications
                FROM lender_county_year
                GROUP BY activity_year
            ),
            missing_lender AS (
                SELECT activity_year, SUM(missing_lender_rows) AS qa_missing_lender_rows
                FROM lender_county_year_missing_lender_qa
                GROUP BY activity_year
            ),
            missing_geo AS (
                SELECT activity_year, SUM(missing_geo_rows) AS qa_missing_geo_rows
                FROM lender_county_year_missing_geo_qa
                GROUP BY activity_year
            )
            SELECT
                source.activity_year,
                source.expected_main_rows,
                main.main_applications,
                main.main_applications - source.expected_main_rows AS main_difference,
                source.expected_missing_lender_rows,
                COALESCE(missing_lender.qa_missing_lender_rows, 0) AS qa_missing_lender_rows,
                COALESCE(missing_lender.qa_missing_lender_rows, 0) - source.expected_missing_lender_rows AS missing_lender_difference,
                source.expected_missing_geo_rows,
                missing_geo.qa_missing_geo_rows,
                missing_geo.qa_missing_geo_rows - source.expected_missing_geo_rows AS missing_geo_difference
            FROM source
            LEFT JOIN main USING (activity_year)
            LEFT JOIN missing_lender USING (activity_year)
            LEFT JOIN missing_geo USING (activity_year)
            ORDER BY source.activity_year;
            """,
        )
        missing_lender_by_year = query_dicts(
            con,
            """
            SELECT
                activity_year,
                COUNT(*) AS county_rows,
                SUM(missing_lender_rows) AS missing_lender_rows,
                SUM(total_loan_amount) AS total_loan_amount
            FROM lender_county_year_missing_lender_qa
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        missing_geo_by_year = query_dicts(
            con,
            """
            SELECT *
            FROM lender_county_year_missing_geo_qa
            ORDER BY activity_year;
            """,
        )
    finally:
        con.close()

    for column in ["row_count", "applications", "originated_loans", "denied_applications"]:
        summary[column] = fmt_int(summary[column])
    summary["total_loan_amount"] = fmt_float(summary["total_loan_amount"])

    format_int_columns(
        by_year,
        [
            "lender_county_rows",
            "county_count",
            "lender_count",
            "applications",
            "originated_loans",
            "denied_applications",
        ],
    )
    format_float_columns(by_year, ["total_loan_amount"])

    for column in key_checks:
        key_checks[column] = fmt_int(key_checks[column])
    duplicate_check["duplicate_grain_rows"] = fmt_int(duplicate_check["duplicate_grain_rows"])

    format_int_columns(
        reconciliation,
        [
            "expected_main_rows",
            "main_applications",
            "main_difference",
            "expected_missing_lender_rows",
            "qa_missing_lender_rows",
            "missing_lender_difference",
            "expected_missing_geo_rows",
            "qa_missing_geo_rows",
            "missing_geo_difference",
        ],
    )
    format_int_columns(missing_lender_by_year, ["county_rows", "missing_lender_rows"])
    format_float_columns(missing_lender_by_year, ["total_loan_amount"])
    format_int_columns(
        missing_geo_by_year,
        [
            "missing_geo_rows",
            "missing_state_fips_2",
            "missing_county_fips_5",
            "missing_lender_id",
            "distinct_lenders",
            "originated_loans",
            "denied_applications",
        ],
    )
    format_float_columns(missing_geo_by_year, ["total_loan_amount"])

    return {
        "objects": objects,
        "summary": summary,
        "by_year": by_year,
        "key_checks": key_checks,
        "duplicate_check": duplicate_check,
        "reconciliation": reconciliation,
        "missing_lender_by_year": missing_lender_by_year,
        "missing_geo_by_year": missing_geo_by_year,
    }


def build_markdown(results: dict[str, Any]) -> str:
    summary = results["summary"]
    lines = [
        "# Lender-County-Year Aggregate",
        "",
        "## Scope",
        "",
        "This step creates the first lender-county-year aggregate from `loan_years_geo`. It does not classify fintech lenders and does not create `county_year_fintech_lending`.",
        "",
        "## Source And Grain",
        "",
        "- Source view: `loan_years_geo`",
        "- Grain: `activity_year`, `state_fips_2`, `county_fips_5`, `lender_id`",
        "- Main-table exclusion rule: rows with missing `county_fips_5` are excluded.",
        "- Main-table exclusion rule: rows with missing or blank `lender_id` are excluded.",
        "- Rows with missing lender IDs but usable county geography are summarized in `lender_county_year_missing_lender_qa`.",
        "- Rows with missing county geography are summarized in `lender_county_year_missing_geo_qa`.",
        "",
        "## Objects Created",
        "",
        markdown_table(results["objects"], ["table_name", "table_type"]),
        "",
        "## Metrics",
        "",
        "- `applications`: count of loan-level rows at the lender-county-year grain.",
        "- `originated_loans`: rows where `action_taken = '1'`.",
        "- `denied_applications`: rows where `action_taken = '3'`.",
        "- `total_loan_amount`: sum of normalized `loan_amount`.",
        "- `average_loan_amount`: average of normalized `loan_amount`.",
        "- `median_loan_amount`: DuckDB `MEDIAN(loan_amount)`.",
        "- `loan_type_1_count` through `loan_type_4_count`, plus `loan_type_other_count`.",
        "- `loan_purpose_1_count`, `loan_purpose_2_count`, `loan_purpose_3_count`, `loan_purpose_31_count`, `loan_purpose_32_count`, `loan_purpose_4_count`, `loan_purpose_5_count`, plus `loan_purpose_other_count`.",
        "",
        "## Summary",
        "",
        f"- Row count: `{summary['row_count']}`",
        f"- Years: `{summary['min_year']}-{summary['max_year']}`",
        f"- Applications: `{summary['applications']}`",
        f"- Originated loans: `{summary['originated_loans']}`",
        f"- Denied applications: `{summary['denied_applications']}`",
        f"- Total loan amount: `{summary['total_loan_amount']}`",
        "",
        "## Key And Grain Checks",
        "",
        markdown_table([results["key_checks"]], list(results["key_checks"].keys())),
        "",
        markdown_table([results["duplicate_check"]], ["duplicate_grain_rows"]),
        "",
        "## Lender-County-Year Counts By Year",
        "",
        markdown_table(
            results["by_year"],
            [
                "activity_year",
                "lender_county_rows",
                "county_count",
                "lender_count",
                "applications",
                "originated_loans",
                "denied_applications",
                "total_loan_amount",
            ],
        ),
        "",
        "## Reconciliation",
        "",
        markdown_table(
            results["reconciliation"],
            [
                "activity_year",
                "expected_main_rows",
                "main_applications",
                "main_difference",
                "expected_missing_lender_rows",
                "qa_missing_lender_rows",
                "missing_lender_difference",
                "expected_missing_geo_rows",
                "qa_missing_geo_rows",
                "missing_geo_difference",
            ],
        ),
        "",
        "## Missing Lender QA",
        "",
    ]
    if results["missing_lender_by_year"]:
        lines.append(
            markdown_table(
                results["missing_lender_by_year"],
                ["activity_year", "county_rows", "missing_lender_rows", "total_loan_amount"],
            )
        )
    else:
        lines.append("No rows with usable county geography and missing lender IDs were found.")
    lines.extend(
        [
            "",
            "## Missing Geography QA",
            "",
            markdown_table(
                results["missing_geo_by_year"],
                [
                    "activity_year",
                    "missing_geo_rows",
                    "missing_state_fips_2",
                    "missing_county_fips_5",
                    "missing_lender_id",
                    "distinct_lenders",
                    "originated_loans",
                    "denied_applications",
                    "total_loan_amount",
                ],
            ),
            "",
            "## Notes",
            "",
            "- `lender_county_year` is suitable for lender-level geography expansion analysis but does not identify fintech lenders.",
            "- Historic respondent IDs and post-2018 LEIs remain different identifier systems; cross-era lender matching requires a separate crosswalk.",
            "- The current canonical database does not include lender names.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build lender-county-year HMDA lending aggregate.")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without modifying the database.")
    args = parser.parse_args()
    if args.dry_run:
        print(LENDER_COUNTY_YEAR_SQL)
        print()
        print(MISSING_LENDER_SQL)
        print()
        print(MISSING_GEO_SQL)
        return 0

    results = build_aggregate()
    DOC_PATH.write_text(build_markdown(results), encoding="utf-8")
    print(f"updated {DB_PATH}")
    print(f"wrote {DOC_PATH}")
    print(f"lender_county_year_rows={results['summary']['row_count']}")
    print("fintech_classification=not_run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
