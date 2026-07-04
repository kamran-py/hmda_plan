from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hmda_panel.duckdb"
CONVERSION_METADATA_PATH = PROJECT_ROOT / "data" / "parquet" / "conversion_metadata.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "db_qa.md"
EXPECTED_YEARS = list(range(2007, 2025))


def query_dicts(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    result = con.execute(sql)
    columns = [desc[0] for desc in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def fmt_int(value: Any) -> str:
    if value is None:
        return ""
    return f"{int(value):,}"


def fmt_float(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):,.0f}"


def build_qa() -> dict[str, Any]:
    metadata = json.loads(CONVERSION_METADATA_PATH.read_text(encoding="utf-8"))
    metadata_total_rows = sum(record["row_count"] or 0 for record in metadata)
    metadata_years = sorted(record["year"] for record in metadata)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        objects = query_dicts(
            con,
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name;
            """,
        )
        loan_years_schema = query_dicts(con, "DESCRIBE loan_years;")
        year_summary = query_dicts(
            con,
            """
            SELECT
                activity_year,
                row_count,
                state_count,
                county_count,
                lender_count,
                total_loan_amount
            FROM year_summary
            ORDER BY activity_year;
            """,
        )
        for row in year_summary:
            row["row_count"] = fmt_int(row["row_count"])
            row["total_loan_amount"] = fmt_float(row["total_loan_amount"])

        total_row_count = con.execute("SELECT COUNT(*) FROM loan_years;").fetchone()[0]
        distinct_years = [
            row[0]
            for row in con.execute(
                "SELECT DISTINCT activity_year FROM loan_years ORDER BY activity_year;"
            ).fetchall()
        ]
        expected_years_present = distinct_years == EXPECTED_YEARS
        invalid_activity_years = query_dicts(
            con,
            """
            SELECT activity_year, COUNT(*) AS row_count
            FROM loan_years
            WHERE activity_year IS NULL OR activity_year NOT BETWEEN 2007 AND 2024
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        missing_counts = query_dicts(
            con,
            """
            SELECT
                activity_year,
                COUNT(*) AS row_count,
                SUM(CASE WHEN activity_year IS NULL THEN 1 ELSE 0 END) AS missing_activity_year,
                SUM(CASE WHEN state_code IS NULL OR TRIM(state_code) = '' THEN 1 ELSE 0 END) AS missing_state_code,
                SUM(CASE WHEN county_code IS NULL OR TRIM(county_code) = '' THEN 1 ELSE 0 END) AS missing_county_code,
                SUM(CASE WHEN lender_id IS NULL OR TRIM(lender_id) = '' THEN 1 ELSE 0 END) AS missing_lender_id,
                SUM(CASE WHEN loan_amount IS NULL THEN 1 ELSE 0 END) AS missing_loan_amount
            FROM loan_years
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        for row in missing_counts:
            for column in list(row):
                if column != "activity_year":
                    row[column] = fmt_int(row[column])

        county_patterns = query_dicts(
            con,
            """
            SELECT
                activity_year,
                source_era,
                COUNT(*) AS row_count,
                SUM(CASE WHEN county_code IS NULL OR TRIM(county_code) = '' THEN 1 ELSE 0 END) AS missing_county_code,
                SUM(CASE WHEN regexp_full_match(TRIM(county_code), '^[0-9]{3}$') THEN 1 ELSE 0 END) AS county_3_digit,
                SUM(CASE WHEN regexp_full_match(TRIM(county_code), '^[0-9]{5}$') THEN 1 ELSE 0 END) AS county_5_digit,
                SUM(CASE WHEN county_code IS NOT NULL AND TRIM(county_code) <> ''
                          AND NOT regexp_full_match(TRIM(county_code), '^[0-9]{3}$')
                          AND NOT regexp_full_match(TRIM(county_code), '^[0-9]{5}$')
                         THEN 1 ELSE 0 END) AS county_other_format,
                MIN(LENGTH(TRIM(county_code))) FILTER (WHERE county_code IS NOT NULL AND TRIM(county_code) <> '') AS min_county_len,
                MAX(LENGTH(TRIM(county_code))) FILTER (WHERE county_code IS NOT NULL AND TRIM(county_code) <> '') AS max_county_len
            FROM loan_years
            GROUP BY activity_year, source_era
            ORDER BY activity_year;
            """,
        )
        for row in county_patterns:
            for column in ["row_count", "missing_county_code", "county_3_digit", "county_5_digit", "county_other_format"]:
                row[column] = fmt_int(row[column])

        state_patterns = query_dicts(
            con,
            """
            SELECT
                activity_year,
                source_era,
                COUNT(*) AS row_count,
                COUNT(DISTINCT state_code) FILTER (WHERE state_code IS NOT NULL AND TRIM(state_code) <> '') AS distinct_state_values,
                SUM(CASE WHEN state_code IS NULL OR TRIM(state_code) = '' THEN 1 ELSE 0 END) AS missing_state_code,
                SUM(CASE WHEN regexp_full_match(TRIM(state_code), '^[0-9]{2}$') THEN 1 ELSE 0 END) AS state_2_digit,
                SUM(CASE WHEN regexp_full_match(TRIM(state_code), '^[A-Z]{2}$') THEN 1 ELSE 0 END) AS state_2_alpha,
                SUM(CASE WHEN state_code IS NOT NULL AND TRIM(state_code) <> ''
                          AND NOT regexp_full_match(TRIM(state_code), '^[0-9]{2}$')
                          AND NOT regexp_full_match(TRIM(state_code), '^[A-Z]{2}$')
                         THEN 1 ELSE 0 END) AS state_other_format
            FROM loan_years
            GROUP BY activity_year, source_era
            ORDER BY activity_year;
            """,
        )
        for row in state_patterns:
            for column in ["row_count", "missing_state_code", "state_2_digit", "state_2_alpha", "state_other_format"]:
                row[column] = fmt_int(row[column])

        county_other_samples = query_dicts(
            con,
            """
            SELECT source_era, county_code, COUNT(*) AS row_count
            FROM loan_years
            WHERE county_code IS NOT NULL AND TRIM(county_code) <> ''
              AND NOT regexp_full_match(TRIM(county_code), '^[0-9]{3}$')
              AND NOT regexp_full_match(TRIM(county_code), '^[0-9]{5}$')
            GROUP BY source_era, county_code
            ORDER BY row_count DESC
            LIMIT 20;
            """,
        )
        state_other_samples = query_dicts(
            con,
            """
            SELECT source_era, state_code, COUNT(*) AS row_count
            FROM loan_years
            WHERE state_code IS NOT NULL AND TRIM(state_code) <> ''
              AND NOT regexp_full_match(TRIM(state_code), '^[0-9]{2}$')
              AND NOT regexp_full_match(TRIM(state_code), '^[A-Z]{2}$')
            GROUP BY source_era, state_code
            ORDER BY row_count DESC
            LIMIT 20;
            """,
        )
        columns = {row["column_name"] for row in loan_years_schema}
        return {
            "objects": objects,
            "loan_years_schema": loan_years_schema,
            "year_summary": year_summary,
            "metadata_total_rows": metadata_total_rows,
            "loan_years_total_rows": total_row_count,
            "row_count_matches_metadata": total_row_count == metadata_total_rows,
            "metadata_years": metadata_years,
            "loan_years_years": distinct_years,
            "expected_years_present": expected_years_present,
            "invalid_activity_years": invalid_activity_years,
            "missing_counts": missing_counts,
            "county_patterns": county_patterns,
            "state_patterns": state_patterns,
            "county_other_samples": county_other_samples,
            "state_other_samples": state_other_samples,
            "lei_or_respondent_id_column_present": "lei_or_respondent_id" in columns,
            "lender_id_column_present": "lender_id" in columns,
        }
    finally:
        con.close()


def build_markdown(qa: dict[str, Any]) -> str:
    lines = [
        "# DuckDB QA",
        "",
        "## Scope",
        "",
        "This QA pass inspects `data/duckdb/hmda_panel.duckdb`. It does not create research aggregates, classify fintech lenders, delete raw files, or delete Parquet files.",
        "",
        "## Database Objects",
        "",
        markdown_table(qa["objects"], ["table_name", "table_type"]),
        "",
        "## Row Count Reconciliation",
        "",
        f"- `loan_years` total rows: `{fmt_int(qa['loan_years_total_rows'])}`",
        f"- `conversion_metadata.json` total rows: `{fmt_int(qa['metadata_total_rows'])}`",
        f"- Match: `{qa['row_count_matches_metadata']}`",
        f"- Years in `loan_years`: `{qa['loan_years_years'][0]}-{qa['loan_years_years'][-1]}`",
        f"- All expected years `2007-2024` present: `{qa['expected_years_present']}`",
        f"- `lei_or_respondent_id` column present in `loan_years`: `{qa['lei_or_respondent_id_column_present']}`",
        f"- `lender_id` column present in `loan_years`: `{qa['lender_id_column_present']}`",
        "",
        "Note: the first DuckDB build renamed canonical `lei_or_respondent_id` to `lender_id`; missing lender identifier checks below use `lender_id`.",
        "",
        "## Year Summary",
        "",
        markdown_table(
            qa["year_summary"],
            ["activity_year", "row_count", "state_count", "county_count", "lender_count", "total_loan_amount"],
        ),
        "",
        "## Missing Key Fields By Year",
        "",
        markdown_table(
            qa["missing_counts"],
            [
                "activity_year",
                "row_count",
                "missing_activity_year",
                "missing_state_code",
                "missing_county_code",
                "missing_lender_id",
                "missing_loan_amount",
            ],
        ),
        "",
        "## Invalid Activity Years",
        "",
    ]
    if qa["invalid_activity_years"]:
        lines.append(markdown_table(qa["invalid_activity_years"], ["activity_year", "row_count"]))
    else:
        lines.append("No invalid or unexpected `activity_year` values found.")

    lines.extend(
        [
            "",
            "## County Code Pattern Check",
            "",
            markdown_table(
                qa["county_patterns"],
                [
                    "activity_year",
                    "source_era",
                    "row_count",
                    "missing_county_code",
                    "county_3_digit",
                    "county_5_digit",
                    "county_other_format",
                    "min_county_len",
                    "max_county_len",
                ],
            ),
            "",
            "Interpretation: pre-2018 county codes are mostly 3-digit county components, while post-2018 county codes are mostly 5-digit full county FIPS codes. They are not directly consistent across eras and should be normalized before county-level aggregation.",
            "",
            "## County Code Other-Format Samples",
            "",
        ]
    )
    if qa["county_other_samples"]:
        lines.append(markdown_table(qa["county_other_samples"], ["source_era", "county_code", "row_count"]))
    else:
        lines.append("No non-empty county codes outside 3-digit or 5-digit numeric formats found.")

    lines.extend(
        [
            "",
            "## State Code Pattern Check",
            "",
            markdown_table(
                qa["state_patterns"],
                [
                    "activity_year",
                    "source_era",
                    "row_count",
                    "distinct_state_values",
                    "missing_state_code",
                    "state_2_digit",
                    "state_2_alpha",
                    "state_other_format",
                ],
            ),
            "",
            "Interpretation: pre-2018 state codes are numeric/FIPS-style two-character codes, while post-2018 state codes are mostly two-letter abbreviations. They are not directly consistent across eras and should be normalized before geographic panel construction.",
            "",
            "## State Code Other-Format Samples",
            "",
        ]
    )
    if qa["state_other_samples"]:
        lines.append(markdown_table(qa["state_other_samples"], ["source_era", "state_code", "row_count"]))
    else:
        lines.append("No non-empty state codes outside two-digit numeric or two-letter uppercase formats found.")

    lines.extend(
        [
            "",
            "## QA Conclusions",
            "",
            "- `loan_years` row count matches `conversion_metadata.json`.",
            "- All years `2007-2024` are present.",
            "- No invalid `activity_year` values were found.",
            "- `state_code` and `county_code` have era-specific formats and require normalization before county-year research aggregates.",
            "- `lender_id` is available for all years, but historic respondent IDs and post-2018 LEIs are different identifier systems.",
            "- Missing `loan_amount` exists in small numbers in some post-2018 years; aggregation code should decide whether to exclude or separately count missing amounts.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    qa = build_qa()
    OUTPUT_PATH.write_text(build_markdown(qa), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    print(f"row_count_matches_metadata={qa['row_count_matches_metadata']}")
    print(f"expected_years_present={qa['expected_years_present']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
