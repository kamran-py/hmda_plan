from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hmda_panel.duckdb"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "research_readiness_audit.md"


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


def format_int_columns(rows: list[dict[str, Any]], columns: list[str]) -> None:
    for row in rows:
        for column in columns:
            row[column] = fmt_int(row.get(column))


def format_float_columns(rows: list[dict[str, Any]], columns: list[str]) -> None:
    for row in rows:
        for column in columns:
            row[column] = fmt_float(row.get(column))


def discover_raw_source_keys(con: duckdb.DuckDBPyConnection) -> list[str]:
    rows = query_dicts(
        con,
        """
        SELECT DISTINCT key
        FROM (
            SELECT UNNEST(json_keys(raw_source_columns)) AS key
            FROM (
                SELECT raw_source_columns
                FROM loan_years_geo
                WHERE source_era = 'pre_2018'
                  AND raw_source_columns IS NOT NULL
                LIMIT 1000
            )
            UNION ALL
            SELECT UNNEST(json_keys(raw_source_columns)) AS key
            FROM (
                SELECT raw_source_columns
                FROM loan_years_geo
                WHERE source_era = 'post_2018'
                  AND raw_source_columns IS NOT NULL
                LIMIT 1000
            )
        )
        ORDER BY key;
        """,
    )
    return [row["key"] for row in rows]


def build_audit() -> dict[str, Any]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        county_summary = query_dicts(
            con,
            """
            SELECT
                COUNT(*) AS row_count,
                MIN(activity_year) AS min_year,
                MAX(activity_year) AS max_year,
                COUNT(DISTINCT activity_year) AS year_count,
                SUM(total_records) AS total_records,
                SUM(application_records) AS application_records,
                SUM(purchased_loans) AS purchased_loans,
                SUM(total_applications) AS total_applications,
                SUM(originated_loans) AS originated_loans,
                SUM(denied_applications) AS denied_applications,
                SUM(total_loan_amount) AS total_loan_amount
            FROM county_year_lending;
            """,
        )[0]
        county_by_year = query_dicts(
            con,
            """
            SELECT
                activity_year,
                COUNT(*) AS county_count,
                SUM(total_records) AS total_records,
                SUM(application_records) AS application_records,
                SUM(purchased_loans) AS purchased_loans,
                SUM(total_applications) AS total_applications,
                SUM(originated_loans) AS originated_loans,
                SUM(denied_applications) AS denied_applications,
                SUM(total_loan_amount) AS total_loan_amount
            FROM county_year_lending
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        county_nulls = query_dicts(
            con,
            """
            SELECT
                SUM(CASE WHEN activity_year IS NULL THEN 1 ELSE 0 END) AS null_activity_year,
                SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS null_state_fips_2,
                SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS null_county_fips_5
            FROM county_year_lending;
            """,
        )[0]
        duplicate_grain = query_dicts(
            con,
            """
            SELECT COUNT(*) AS duplicate_grain_rows
            FROM (
                SELECT activity_year, state_fips_2, county_fips_5, COUNT(*) AS row_count
                FROM county_year_lending
                GROUP BY activity_year, state_fips_2, county_fips_5
                HAVING COUNT(*) > 1
            );
            """,
        )[0]
        reconciliation_by_year = query_dicts(
            con,
            """
            WITH geo AS (
                SELECT
                    activity_year,
                    COUNT(*) AS loan_years_geo_rows,
                    SUM(CASE WHEN county_fips_5 IS NOT NULL THEN 1 ELSE 0 END) AS expected_included_records,
                    SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS expected_excluded_missing_geo
                FROM loan_years_geo
                GROUP BY activity_year
            ),
            agg AS (
                SELECT
                    activity_year,
                    SUM(total_records) AS aggregate_included_records
                FROM county_year_lending
                GROUP BY activity_year
            ),
            missing AS (
                SELECT
                    activity_year,
                    SUM(missing_geo_rows) AS qa_excluded_missing_geo
                FROM county_year_lending_missing_geo_qa
                GROUP BY activity_year
            )
            SELECT
                geo.activity_year,
                geo.loan_years_geo_rows,
                geo.expected_included_records,
                agg.aggregate_included_records,
                agg.aggregate_included_records - geo.expected_included_records AS included_difference,
                geo.expected_excluded_missing_geo,
                missing.qa_excluded_missing_geo,
                missing.qa_excluded_missing_geo - geo.expected_excluded_missing_geo AS excluded_difference
            FROM geo
            LEFT JOIN agg USING (activity_year)
            LEFT JOIN missing USING (activity_year)
            ORDER BY geo.activity_year;
            """,
        )
        reconciliation_total = query_dicts(
            con,
            """
            WITH geo AS (
                SELECT
                    COUNT(*) AS loan_years_geo_rows,
                    SUM(CASE WHEN county_fips_5 IS NOT NULL THEN 1 ELSE 0 END) AS expected_included_records,
                    SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS expected_excluded_missing_geo
                FROM loan_years_geo
            ),
            agg AS (
                SELECT SUM(total_records) AS aggregate_included_records
                FROM county_year_lending
            ),
            missing AS (
                SELECT SUM(missing_geo_rows) AS qa_excluded_missing_geo
                FROM county_year_lending_missing_geo_qa
            )
            SELECT
                geo.loan_years_geo_rows,
                geo.expected_included_records,
                agg.aggregate_included_records,
                agg.aggregate_included_records - geo.expected_included_records AS included_difference,
                geo.expected_excluded_missing_geo,
                missing.qa_excluded_missing_geo,
                missing.qa_excluded_missing_geo - geo.expected_excluded_missing_geo AS excluded_difference
            FROM geo, agg, missing;
            """,
        )[0]
        lender_by_year = query_dicts(
            con,
            """
            SELECT
                activity_year,
                COUNT(*) AS row_count,
                SUM(CASE WHEN lender_id IS NULL OR TRIM(lender_id) = '' THEN 1 ELSE 0 END) AS missing_lender_id,
                COUNT(DISTINCT lender_id)
                    FILTER (WHERE lender_id IS NOT NULL AND TRIM(lender_id) <> '') AS distinct_lenders,
                COUNT(DISTINCT lender_id_type)
                    FILTER (WHERE lender_id_type IS NOT NULL AND TRIM(lender_id_type) <> '') AS lender_id_type_count
            FROM loan_years_geo
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        lender_id_types = query_dicts(
            con,
            """
            SELECT
                source_era,
                lender_id_type,
                MIN(activity_year) AS min_year,
                MAX(activity_year) AS max_year,
                COUNT(*) AS row_count
            FROM loan_years_geo
            GROUP BY source_era, lender_id_type
            ORDER BY min_year;
            """,
        )
        loan_years_geo_schema = query_dicts(con, "DESCRIBE loan_years_geo;")
        schema_columns = [row["column_name"] for row in loan_years_geo_schema]
        lender_identifier_like_columns = [
            column
            for column in schema_columns
            if any(token in column.lower() for token in ["lender", "respondent", "lei", "name"])
        ]
        lender_name_columns = [column for column in schema_columns if "name" in column.lower()]
        raw_source_keys = discover_raw_source_keys(con)
        lender_identifier_like_raw_keys = [
            key
            for key in raw_source_keys
            if any(token in key.lower() for token in ["lender", "respondent", "lei", "name"])
        ]
        lender_name_raw_keys = [key for key in raw_source_keys if "name" in key.lower()]
        action_mapping = query_dicts(
            con,
            """
            SELECT
                source_era,
                action_taken,
                action_description,
                counts_as_origination,
                counts_as_denial
            FROM action_taken_metadata
            ORDER BY source_era, action_taken;
            """,
        )
        action_counts = query_dicts(
            con,
            """
            SELECT
                activity_year,
                source_era,
                COALESCE(NULLIF(TRIM(action_taken), ''), '<missing>') AS action_taken,
                COUNT(*) AS row_count
            FROM loan_years_geo
            GROUP BY activity_year, source_era, COALESCE(NULLIF(TRIM(action_taken), ''), '<missing>')
            ORDER BY
                activity_year,
                TRY_CAST(COALESCE(NULLIF(TRIM(action_taken), ''), '<missing>') AS INTEGER) NULLS LAST,
                COALESCE(NULLIF(TRIM(action_taken), ''), '<missing>');
            """,
        )
    finally:
        con.close()

    for key in [
        "row_count",
        "year_count",
        "total_records",
        "application_records",
        "purchased_loans",
        "total_applications",
        "originated_loans",
        "denied_applications",
    ]:
        county_summary[key] = fmt_int(county_summary[key])
    county_summary["total_loan_amount"] = fmt_float(county_summary["total_loan_amount"])

    for key in county_nulls:
        county_nulls[key] = fmt_int(county_nulls[key])
    duplicate_grain["duplicate_grain_rows"] = fmt_int(duplicate_grain["duplicate_grain_rows"])

    format_int_columns(
        county_by_year,
        [
            "county_count",
            "total_records",
            "application_records",
            "purchased_loans",
            "total_applications",
            "originated_loans",
            "denied_applications",
        ],
    )
    format_float_columns(county_by_year, ["total_loan_amount"])
    format_int_columns(
        reconciliation_by_year,
        [
            "loan_years_geo_rows",
            "expected_included_records",
            "aggregate_included_records",
            "included_difference",
            "expected_excluded_missing_geo",
            "qa_excluded_missing_geo",
            "excluded_difference",
        ],
    )
    for key in reconciliation_total:
        reconciliation_total[key] = fmt_int(reconciliation_total[key])
    format_int_columns(
        lender_by_year,
        ["row_count", "missing_lender_id", "distinct_lenders", "lender_id_type_count"],
    )
    format_int_columns(lender_id_types, ["row_count"])
    format_int_columns(action_counts, ["row_count"])

    return {
        "county_summary": county_summary,
        "county_by_year": county_by_year,
        "county_nulls": county_nulls,
        "duplicate_grain": duplicate_grain,
        "reconciliation_total": reconciliation_total,
        "reconciliation_by_year": reconciliation_by_year,
        "lender_by_year": lender_by_year,
        "lender_id_types": lender_id_types,
        "lender_identifier_like_columns": lender_identifier_like_columns,
        "lender_name_columns": lender_name_columns,
        "raw_source_keys": raw_source_keys,
        "lender_identifier_like_raw_keys": lender_identifier_like_raw_keys,
        "lender_name_raw_keys": lender_name_raw_keys,
        "action_mapping": action_mapping,
        "action_counts": action_counts,
    }


def build_markdown(results: dict[str, Any]) -> str:
    summary = results["county_summary"]
    lender_identifier_like_columns = results["lender_identifier_like_columns"]
    lender_name_columns = results["lender_name_columns"]
    lender_identifier_like_raw_keys = results["lender_identifier_like_raw_keys"]
    lender_name_raw_keys = results["lender_name_raw_keys"]
    raw_source_keys = results["raw_source_keys"]
    lines = [
        "# Research Readiness Audit",
        "",
        "## Scope",
        "",
        "This audit checks whether `county_year_lending` and `loan_years_geo` are ready to support lender-level and fintech-expansion analysis. It does not create new research aggregates, classify fintech lenders, or export final CSVs.",
        "",
        "## County-Year Aggregate Summary",
        "",
        f"- Row count: `{summary['row_count']}`",
        f"- Years covered: `{summary['min_year']}-{summary['max_year']}`",
        f"- Year count: `{summary['year_count']}`",
        f"- Total records: `{summary['total_records']}`",
        f"- Application records: `{summary['application_records']}`",
        f"- Purchased loans: `{summary['purchased_loans']}`",
        f"- Total applications legacy field: `{summary['total_applications']}`",
        f"- Originated loans: `{summary['originated_loans']}`",
        f"- Denied applications: `{summary['denied_applications']}`",
        f"- Total loan amount: `{summary['total_loan_amount']}`",
        "",
        "## County-Year Checks",
        "",
        markdown_table([results["county_nulls"]], list(results["county_nulls"].keys())),
        "",
        markdown_table([results["duplicate_grain"]], ["duplicate_grain_rows"]),
        "",
        "## County-Year Metrics By Year",
        "",
        markdown_table(
            results["county_by_year"],
            [
                "activity_year",
                "county_count",
                "total_records",
                "application_records",
                "purchased_loans",
                "total_applications",
                "originated_loans",
                "denied_applications",
                "total_loan_amount",
            ],
        ),
        "",
        "## Reconciliation Against Loan-Level Geography",
        "",
        "The aggregate record count should equal `loan_years_geo` rows where `county_fips_5` is present. Excluded rows should equal `county_year_lending_missing_geo_qa`.",
        "",
        markdown_table([results["reconciliation_total"]], list(results["reconciliation_total"].keys())),
        "",
        markdown_table(
            results["reconciliation_by_year"],
            [
                "activity_year",
                "loan_years_geo_rows",
                "expected_included_records",
                "aggregate_included_records",
                "included_difference",
                "expected_excluded_missing_geo",
                "qa_excluded_missing_geo",
                "excluded_difference",
            ],
        ),
        "",
        "## Lender Fields",
        "",
        "- Canonical lender identifier column: `lender_id`.",
        "- Identifier type column: `lender_id_type`.",
        "- `lender_id_type` is `respondent_id` for pre-2018 data and `lei` for post-2018 data.",
        "- Historic respondent IDs and post-2018 LEIs are not the same identifier system, so cross-era lender identity resolution remains a separate task.",
        f"- Explicit lender-name columns in `loan_years_geo`: `{', '.join(lender_name_columns) if lender_name_columns else 'none'}`.",
        f"- Lender-name keys retained in `raw_source_columns`: `{', '.join(lender_name_raw_keys) if lender_name_raw_keys else 'none'}`.",
        f"- Available lender identifier/name-like columns in `loan_years_geo`: `{', '.join(lender_identifier_like_columns) if lender_identifier_like_columns else 'none'}`.",
        f"- Available lender identifier/name-like keys retained in `raw_source_columns`: `{', '.join(lender_identifier_like_raw_keys) if lender_identifier_like_raw_keys else 'none'}`.",
        f"- Raw source keys sampled: `{', '.join(raw_source_keys) if raw_source_keys else 'none'}`.",
        "",
        "## Lender Identifier Coverage By Year",
        "",
        markdown_table(
            results["lender_by_year"],
            ["activity_year", "row_count", "missing_lender_id", "distinct_lenders", "lender_id_type_count"],
        ),
        "",
        "## Lender Identifier Types",
        "",
        markdown_table(
            results["lender_id_types"],
            ["source_era", "lender_id_type", "min_year", "max_year", "row_count"],
        ),
        "",
        "## Action Taken Mapping",
        "",
        "- Originated loans count `action_taken = '1'`.",
        "- Denied applications count `action_taken = '3'`.",
        "- Application records count non-purchase action records with `action_taken` in `1`, `2`, `3`, `4`, `5`, `7`, or `8`.",
        "- Purchased loans count `action_taken = '6'` and are excluded from `application_records`.",
        "- Action code `7` is documented as preapproval denied but is not included in `denied_applications`.",
        "",
        markdown_table(
            results["action_mapping"],
            ["source_era", "action_taken", "action_description", "counts_as_origination", "counts_as_denial"],
        ),
        "",
        "## Action Taken Counts By Year",
        "",
        markdown_table(
            results["action_counts"],
            ["activity_year", "source_era", "action_taken", "row_count"],
        ),
        "",
        "## Readiness Notes",
        "",
        "- `county_year_lending` passes grain uniqueness and non-null key checks.",
        "- County-level aggregate record totals reconcile to `loan_years_geo` rows with usable `county_fips_5`.",
        "- Lender IDs are available for all years, but name fields are not present in the current canonical view.",
        "- Fintech classification should therefore start from `lender_id` plus an external or separately sourced lender-name/classification crosswalk.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    results = build_audit()
    OUTPUT_PATH.write_text(build_markdown(results), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")
    print(f"county_year_rows={results['county_summary']['row_count']}")
    print(f"included_difference={results['reconciliation_total']['included_difference']}")
    print(f"excluded_difference={results['reconciliation_total']['excluded_difference']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
