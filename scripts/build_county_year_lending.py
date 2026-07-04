from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hmda_panel.duckdb"
DOC_PATH = PROJECT_ROOT / "docs" / "county_year_lending.md"


COUNTY_YEAR_SQL = """
CREATE OR REPLACE TABLE county_year_lending AS
SELECT
    activity_year,
    state_fips_2,
    county_fips_5,
    COUNT(*) AS total_records,
    SUM(
        CASE
            WHEN TRIM(action_taken) IN ('1', '2', '3', '4', '5', '7', '8')
            THEN 1
            ELSE 0
        END
    ) AS application_records,
    SUM(CASE WHEN TRIM(action_taken) = '6' THEN 1 ELSE 0 END) AS purchased_loans,
    COUNT(*) AS total_applications,
    SUM(CASE WHEN TRIM(action_taken) = '1' THEN 1 ELSE 0 END) AS originated_loans,
    SUM(CASE WHEN TRIM(action_taken) = '3' THEN 1 ELSE 0 END) AS denied_applications,
    SUM(loan_amount) AS total_loan_amount,
    AVG(loan_amount) AS average_loan_amount,
    MEDIAN(loan_amount) AS median_loan_amount,
    COUNT(DISTINCT lender_id)
        FILTER (WHERE lender_id IS NOT NULL AND TRIM(lender_id) <> '') AS lender_count
FROM loan_years_geo
WHERE county_fips_5 IS NOT NULL
GROUP BY activity_year, state_fips_2, county_fips_5
ORDER BY activity_year, state_fips_2, county_fips_5;
""".strip()


MISSING_GEO_SQL = """
CREATE OR REPLACE TABLE county_year_lending_missing_geo_qa AS
SELECT
    activity_year,
    COUNT(*) AS missing_geo_rows,
    SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS missing_state_fips_2,
    SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS missing_county_fips_5,
    COUNT(DISTINCT lender_id)
        FILTER (WHERE lender_id IS NOT NULL AND TRIM(lender_id) <> '') AS lender_count,
    SUM(loan_amount) AS total_loan_amount
FROM loan_years_geo
WHERE county_fips_5 IS NULL
GROUP BY activity_year
ORDER BY activity_year;
""".strip()


ACTION_MAPPING_SQL = """
CREATE OR REPLACE TABLE action_taken_metadata AS
SELECT *
FROM (
    VALUES
        ('pre_2018', '1', 'Loan originated', TRUE, FALSE),
        ('pre_2018', '2', 'Application approved but not accepted', FALSE, FALSE),
        ('pre_2018', '3', 'Application denied', FALSE, TRUE),
        ('pre_2018', '4', 'Application withdrawn by applicant', FALSE, FALSE),
        ('pre_2018', '5', 'File closed for incompleteness', FALSE, FALSE),
        ('pre_2018', '6', 'Loan purchased by institution', FALSE, FALSE),
        ('pre_2018', '7', 'Preapproval request denied', FALSE, FALSE),
        ('pre_2018', '8', 'Preapproval request approved but not accepted', FALSE, FALSE),
        ('post_2018', '1', 'Loan originated', TRUE, FALSE),
        ('post_2018', '2', 'Application approved but not accepted', FALSE, FALSE),
        ('post_2018', '3', 'Application denied', FALSE, TRUE),
        ('post_2018', '4', 'Application withdrawn by applicant', FALSE, FALSE),
        ('post_2018', '5', 'File closed for incompleteness', FALSE, FALSE),
        ('post_2018', '6', 'Loan purchased by institution', FALSE, FALSE),
        ('post_2018', '7', 'Preapproval request denied', FALSE, FALSE),
        ('post_2018', '8', 'Preapproval request approved but not accepted', FALSE, FALSE)
) AS t(source_era, action_taken, action_description, counts_as_origination, counts_as_denial);
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


def build_aggregate() -> dict[str, Any]:
    con = duckdb.connect(str(DB_PATH))
    try:
        con.execute(ACTION_MAPPING_SQL)
        con.execute(COUNTY_YEAR_SQL)
        con.execute(MISSING_GEO_SQL)

        aggregate_summary = query_dicts(
            con,
            """
            SELECT
                COUNT(*) AS aggregate_row_count,
                MIN(activity_year) AS min_year,
                MAX(activity_year) AS max_year,
                SUM(total_applications) AS included_applications,
                SUM(total_records) AS included_records,
                SUM(application_records) AS included_application_records,
                SUM(purchased_loans) AS purchased_loans,
                SUM(originated_loans) AS originated_loans,
                SUM(denied_applications) AS denied_applications
            FROM county_year_lending;
            """,
        )[0]
        county_count_by_year = query_dicts(
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
        geography_consistency = query_dicts(
            con,
            """
            SELECT
                activity_year,
                COUNT(*) AS aggregate_rows,
                COUNT(DISTINCT county_fips_5) AS distinct_county_fips_5,
                SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS rows_with_null_state_fips_2,
                SUM(
                    CASE
                        WHEN state_fips_2 IS NOT NULL
                         AND SUBSTR(county_fips_5, 1, 2) <> state_fips_2
                        THEN 1
                        ELSE 0
                    END
                ) AS state_county_prefix_mismatches
            FROM county_year_lending
            GROUP BY activity_year
            ORDER BY activity_year;
            """,
        )
        missing_geo = query_dicts(
            con,
            """
            SELECT *
            FROM county_year_lending_missing_geo_qa
            ORDER BY activity_year;
            """,
        )
        action_mapping = query_dicts(
            con,
            """
            SELECT *
            FROM action_taken_metadata
            ORDER BY source_era, action_taken;
            """,
        )
        objects = query_dicts(
            con,
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name IN (
                'county_year_lending',
                'county_year_lending_missing_geo_qa',
                'action_taken_metadata'
              )
            ORDER BY table_name;
            """,
        )
    finally:
        con.close()

    for row in county_count_by_year:
        for column in [
            "county_count",
            "total_records",
            "application_records",
            "purchased_loans",
            "total_applications",
            "originated_loans",
            "denied_applications",
        ]:
            row[column] = fmt_int(row[column])
        row["total_loan_amount"] = fmt_float(row["total_loan_amount"])

    for row in geography_consistency:
        for column in [
            "aggregate_rows",
            "distinct_county_fips_5",
            "rows_with_null_state_fips_2",
            "state_county_prefix_mismatches",
        ]:
            row[column] = fmt_int(row[column])

    for row in missing_geo:
        for column in ["missing_geo_rows", "missing_state_fips_2", "missing_county_fips_5", "lender_count"]:
            row[column] = fmt_int(row[column])
        row["total_loan_amount"] = fmt_float(row["total_loan_amount"])

    for column in [
        "aggregate_row_count",
        "included_applications",
        "included_records",
        "included_application_records",
        "purchased_loans",
        "originated_loans",
        "denied_applications",
    ]:
        aggregate_summary[column] = fmt_int(aggregate_summary[column])

    return {
        "objects": objects,
        "aggregate_summary": aggregate_summary,
        "county_count_by_year": county_count_by_year,
        "geography_consistency": geography_consistency,
        "missing_geo": missing_geo,
        "action_mapping": action_mapping,
    }


def build_markdown(results: dict[str, Any]) -> str:
    summary = results["aggregate_summary"]
    lines = [
        "# County-Year Lending Aggregate",
        "",
        "## Scope",
        "",
        "This step creates the first county-year lending aggregate from `loan_years_geo`. It does not classify fintech lenders, delete raw files, delete Parquet files, or create final research-specific aggregates.",
        "",
        "## Source And Grain",
        "",
        "- Source view: `loan_years_geo`",
        "- Grain: `activity_year`, `state_fips_2`, `county_fips_5`",
        "- Exclusion rule: rows with null `county_fips_5` are excluded from `county_year_lending` and summarized separately in `county_year_lending_missing_geo_qa`.",
        "",
        "## Objects Created",
        "",
        markdown_table(results["objects"], ["table_name", "table_type"]),
        "",
        "## Metrics",
        "",
        "- `total_records`: count of loan-level HMDA records at the county-year grain.",
        "- `application_records`: count of non-purchase action records with `action_taken` in `1`, `2`, `3`, `4`, `5`, `7`, or `8`.",
        "- `purchased_loans`: rows where `action_taken = '6'`.",
        "- `total_applications`: legacy alias for `total_records`, retained for backward compatibility with the first public export.",
        "- `originated_loans`: rows where `action_taken = '1'`.",
        "- `denied_applications`: rows where `action_taken = '3'`.",
        "- `total_loan_amount`: sum of normalized `loan_amount`.",
        "- `average_loan_amount`: average of normalized `loan_amount`.",
        "- `median_loan_amount`: DuckDB `MEDIAN(loan_amount)`.",
        "- `lender_count`: distinct non-empty `lender_id`.",
        "",
        "## Action Taken Mapping",
        "",
        markdown_table(
            results["action_mapping"],
            ["source_era", "action_taken", "action_description", "counts_as_origination", "counts_as_denial"],
        ),
        "",
        "## Aggregate Summary",
        "",
        f"- Aggregate row count: `{summary['aggregate_row_count']}`",
        f"- Years: `{summary['min_year']}-{summary['max_year']}`",
        f"- Included records: `{summary['included_records']}`",
        f"- Application records: `{summary['included_application_records']}`",
        f"- Purchased loans: `{summary['purchased_loans']}`",
        f"- Included applications legacy field: `{summary['included_applications']}`",
        f"- Originated loans: `{summary['originated_loans']}`",
        f"- Denied applications: `{summary['denied_applications']}`",
        "",
        "## County Count By Year",
        "",
        markdown_table(
            results["county_count_by_year"],
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
        "## Geography Consistency QA",
        "",
        "Because the aggregate grain includes both `state_fips_2` and `county_fips_5`, the aggregate row count can exceed the distinct `county_fips_5` count when source geography has a null state or a state/county prefix mismatch. These rows are retained in the first aggregate for transparency and should be reviewed before research use.",
        "",
        markdown_table(
            results["geography_consistency"],
            [
                "activity_year",
                "aggregate_rows",
                "distinct_county_fips_5",
                "rows_with_null_state_fips_2",
                "state_county_prefix_mismatches",
            ],
        ),
        "",
        "## Missing Geography Exclusions",
        "",
        markdown_table(
            results["missing_geo"],
            [
                "activity_year",
                "missing_geo_rows",
                "missing_state_fips_2",
                "missing_county_fips_5",
                "lender_count",
                "total_loan_amount",
            ],
        ),
        "",
        "## Notes",
        "",
        "- `county_year_lending` is the first geography-normalized aggregate and should be QAed before adding fintech lender classifications.",
        "- The preferred denominator for application-style rates is `application_records`; `total_records` also includes purchased-loan records.",
        "- Missing-geography rows are not discarded silently; they are tracked in `county_year_lending_missing_geo_qa`.",
        "- Action code `7` is documented as a preapproval denial but is not included in `denied_applications`, which uses application denial code `3`.",
        "- Historic respondent IDs and post-2018 LEIs remain different identifier systems, so `lender_count` is useful within-year but not a cross-era lender identity resolution.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build county-year HMDA lending aggregate.")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without modifying the database.")
    args = parser.parse_args()
    if args.dry_run:
        print(ACTION_MAPPING_SQL)
        print()
        print(COUNTY_YEAR_SQL)
        print()
        print(MISSING_GEO_SQL)
        return 0

    results = build_aggregate()
    DOC_PATH.write_text(build_markdown(results), encoding="utf-8")
    print(f"updated {DB_PATH}")
    print(f"wrote {DOC_PATH}")
    print(f"aggregate_rows={results['aggregate_summary']['aggregate_row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
