from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hmda_panel.duckdb"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "geography_normalization.md"


STATE_CROSSWALK = [
    ("01", "AL", "Alabama"),
    ("02", "AK", "Alaska"),
    ("04", "AZ", "Arizona"),
    ("05", "AR", "Arkansas"),
    ("06", "CA", "California"),
    ("08", "CO", "Colorado"),
    ("09", "CT", "Connecticut"),
    ("10", "DE", "Delaware"),
    ("11", "DC", "District of Columbia"),
    ("12", "FL", "Florida"),
    ("13", "GA", "Georgia"),
    ("15", "HI", "Hawaii"),
    ("16", "ID", "Idaho"),
    ("17", "IL", "Illinois"),
    ("18", "IN", "Indiana"),
    ("19", "IA", "Iowa"),
    ("20", "KS", "Kansas"),
    ("21", "KY", "Kentucky"),
    ("22", "LA", "Louisiana"),
    ("23", "ME", "Maine"),
    ("24", "MD", "Maryland"),
    ("25", "MA", "Massachusetts"),
    ("26", "MI", "Michigan"),
    ("27", "MN", "Minnesota"),
    ("28", "MS", "Mississippi"),
    ("29", "MO", "Missouri"),
    ("30", "MT", "Montana"),
    ("31", "NE", "Nebraska"),
    ("32", "NV", "Nevada"),
    ("33", "NH", "New Hampshire"),
    ("34", "NJ", "New Jersey"),
    ("35", "NM", "New Mexico"),
    ("36", "NY", "New York"),
    ("37", "NC", "North Carolina"),
    ("38", "ND", "North Dakota"),
    ("39", "OH", "Ohio"),
    ("40", "OK", "Oklahoma"),
    ("41", "OR", "Oregon"),
    ("42", "PA", "Pennsylvania"),
    ("44", "RI", "Rhode Island"),
    ("45", "SC", "South Carolina"),
    ("46", "SD", "South Dakota"),
    ("47", "TN", "Tennessee"),
    ("48", "TX", "Texas"),
    ("49", "UT", "Utah"),
    ("50", "VT", "Vermont"),
    ("51", "VA", "Virginia"),
    ("53", "WA", "Washington"),
    ("54", "WV", "West Virginia"),
    ("55", "WI", "Wisconsin"),
    ("56", "WY", "Wyoming"),
    ("60", "AS", "American Samoa"),
    ("66", "GU", "Guam"),
    ("69", "MP", "Northern Mariana Islands"),
    ("72", "PR", "Puerto Rico"),
    ("78", "VI", "U.S. Virgin Islands"),
]


CREATE_VIEW_SQL = """
CREATE OR REPLACE VIEW loan_years_geo AS
WITH cleaned AS (
    SELECT
        loan_years.*,
        UPPER(TRIM(state_code)) AS state_code_clean,
        UPPER(TRIM(county_code)) AS county_code_clean
    FROM loan_years
),
state_from_code AS (
    SELECT
        cleaned.*,
        CASE
            WHEN state_code_clean IS NULL
              OR state_code_clean = ''
              OR state_code_clean = 'NA'
                THEN NULL
            WHEN regexp_full_match(state_code_clean, '^[0-9]{1,2}$')
                THEN LPAD(state_code_clean, 2, '0')
            WHEN regexp_full_match(state_code_clean, '^[A-Z]{2}$')
                THEN state_abbr_xwalk.state_fips
            ELSE NULL
        END AS state_fips_from_state_code,
        CASE
            WHEN state_code_clean IS NULL
              OR state_code_clean = ''
              OR state_code_clean = 'NA'
                THEN 'missing_state_code'
            WHEN regexp_full_match(state_code_clean, '^[0-9]{1,2}$')
                THEN 'state_code_numeric'
            WHEN regexp_full_match(state_code_clean, '^[A-Z]{2}$')
             AND state_abbr_xwalk.state_fips IS NOT NULL
                THEN 'state_code_abbr'
            WHEN regexp_full_match(state_code_clean, '^[A-Z]{2}$')
                THEN 'unmapped_state_code_abbr'
            ELSE 'unmapped_state_code'
        END AS state_code_source
    FROM cleaned
    LEFT JOIN state_fips_crosswalk AS state_abbr_xwalk
        ON cleaned.state_code_clean = state_abbr_xwalk.state_abbr
),
county_from_code AS (
    SELECT
        state_from_code.*,
        CASE
            WHEN regexp_full_match(county_code_clean, '^[0-9]{5}$')
                THEN county_code_clean
            ELSE NULL
        END AS county_code_5_raw,
        CASE
            WHEN regexp_full_match(county_code_clean, '^[0-9]{5}$')
                THEN SUBSTR(county_code_clean, 1, 2)
            ELSE NULL
        END AS county_code_prefix_2,
        CASE
            WHEN regexp_full_match(county_code_clean, '^[0-9]{5}$')
                THEN RIGHT(county_code_clean, 3)
            ELSE NULL
        END AS county_code_suffix_3
    FROM state_from_code
),
county_validated AS (
    SELECT
        county_from_code.*,
        county_prefix_xwalk.state_fips IS NOT NULL
            AND county_code_suffix_3 IS NOT NULL
            AND county_code_suffix_3 <> '000' AS county_fips_5_valid_state_prefix
    FROM county_from_code
    LEFT JOIN state_fips_crosswalk AS county_prefix_xwalk
        ON county_from_code.county_code_prefix_2 = county_prefix_xwalk.state_fips
),
state_norm AS (
    SELECT
        county_validated.*,
        CASE
            WHEN source_era = 'post_2018'
             AND county_fips_5_valid_state_prefix
             AND state_fips_from_state_code IS NULL
                THEN county_code_prefix_2
            WHEN source_era = 'post_2018'
             AND county_fips_5_valid_state_prefix
             AND state_fips_from_state_code <> county_code_prefix_2
                THEN county_code_prefix_2
            ELSE state_fips_from_state_code
        END AS state_fips_2,
        CASE
            WHEN source_era = 'post_2018'
             AND county_fips_5_valid_state_prefix
             AND state_fips_from_state_code IS NULL
                THEN 'county_code_prefix_missing_or_unmapped_state_code'
            WHEN source_era = 'post_2018'
             AND county_fips_5_valid_state_prefix
             AND state_fips_from_state_code <> county_code_prefix_2
                THEN 'county_code_prefix_conflict_with_state_code'
            WHEN state_fips_from_state_code IS NOT NULL
                THEN state_code_source
            ELSE state_code_source
        END AS state_fips_2_source,
        CASE
            WHEN source_era = 'post_2018'
             AND county_fips_5_valid_state_prefix
             AND (
                state_fips_from_state_code IS NULL
                OR state_fips_from_state_code <> county_code_prefix_2
             )
                THEN TRUE
            ELSE FALSE
        END AS state_fips_2_from_county_prefix
    FROM county_validated
)
SELECT
    activity_year,
    source_era,
    lender_id,
    lender_id_type,
    state_code,
    county_code,
    state_fips_2,
    state_fips_2_source,
    state_fips_2_from_county_prefix,
    CASE
        WHEN county_fips_5_valid_state_prefix
            THEN county_code_suffix_3
        WHEN regexp_full_match(county_code_clean, '^[0-9]{1,3}$')
            THEN LPAD(county_code_clean, 3, '0')
        ELSE NULL
    END AS county_fips_3,
    CASE
        WHEN county_fips_5_valid_state_prefix
            THEN county_code_5_raw
        WHEN regexp_full_match(county_code_clean, '^[0-9]{1,3}$')
             AND state_fips_2 IS NOT NULL
            THEN state_fips_2 || LPAD(county_code_clean, 3, '0')
        ELSE NULL
    END AS county_fips_5,
    CASE
        WHEN county_fips_5_valid_state_prefix
            THEN 'county_code_5'
        WHEN regexp_full_match(county_code_clean, '^[0-9]{1,3}$')
             AND state_fips_2 IS NOT NULL
            THEN 'state_county_components'
        WHEN county_code_clean IS NULL
          OR county_code_clean = ''
          OR county_code_clean = 'NA'
            THEN 'missing_county_code'
        WHEN regexp_full_match(county_code_clean, '^[0-9]{5}$')
            THEN 'invalid_county_code_5'
        ELSE 'unmapped_county_code'
    END AS county_fips_5_source,
    county_fips_5_valid_state_prefix,
    census_tract,
    loan_amount,
    loan_type,
    loan_purpose,
    occupancy_type,
    action_taken,
    applicant_income,
    raw_source_columns
FROM state_norm;
""".strip()


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


def create_crosswalk(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE TABLE state_fips_crosswalk (
            state_fips VARCHAR,
            state_abbr VARCHAR,
            state_name VARCHAR
        );
        """
    )
    con.executemany("INSERT INTO state_fips_crosswalk VALUES (?, ?, ?)", STATE_CROSSWALK)


def create_normalized_view(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(CREATE_VIEW_SQL)


def inspect_current_formats(con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    rows = query_dicts(
        con,
        """
        SELECT
            activity_year,
            source_era,
            COUNT(*) AS row_count,
            COUNT(DISTINCT state_code) FILTER (WHERE state_code IS NOT NULL AND TRIM(state_code) <> '') AS distinct_state_values,
            COUNT(DISTINCT county_code) FILTER (WHERE county_code IS NOT NULL AND TRIM(county_code) <> '') AS distinct_county_values,
            SUM(CASE WHEN regexp_full_match(TRIM(state_code), '^[0-9]{1,2}$') THEN 1 ELSE 0 END) AS state_numeric_1_2,
            SUM(CASE WHEN regexp_full_match(TRIM(state_code), '^[A-Z]{2}$') THEN 1 ELSE 0 END) AS state_alpha_2,
            SUM(CASE WHEN state_code IS NULL OR TRIM(state_code) = '' OR UPPER(TRIM(state_code)) = 'NA' THEN 1 ELSE 0 END) AS state_missing_or_na,
            SUM(CASE WHEN regexp_full_match(TRIM(county_code), '^[0-9]{1,3}$') THEN 1 ELSE 0 END) AS county_numeric_1_3,
            SUM(CASE WHEN regexp_full_match(TRIM(county_code), '^[0-9]{5}$') THEN 1 ELSE 0 END) AS county_numeric_5,
            SUM(CASE WHEN county_code IS NULL OR TRIM(county_code) = '' OR UPPER(TRIM(county_code)) = 'NA' THEN 1 ELSE 0 END) AS county_missing_or_na
        FROM loan_years
        GROUP BY activity_year, source_era
        ORDER BY activity_year;
        """,
    )
    for row in rows:
        for key, value in list(row.items()):
            if key not in {"activity_year", "source_era"}:
                row[key] = fmt_int(value)
    return rows


def validate_normalization(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    missing = query_dicts(
        con,
        """
        SELECT
            activity_year,
            COUNT(*) AS row_count,
            SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS missing_state_fips_2,
            SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS missing_county_fips_5,
            SUM(CASE WHEN county_fips_5 IS NOT NULL AND state_fips_2 IS NULL THEN 1 ELSE 0 END) AS county_present_state_missing,
            SUM(
                CASE
                    WHEN county_fips_5 IS NOT NULL
                     AND state_fips_2 IS NOT NULL
                     AND SUBSTR(county_fips_5, 1, 2) <> state_fips_2
                    THEN 1
                    ELSE 0
                END
            ) AS state_county_prefix_mismatches,
            SUM(CASE WHEN state_fips_2_from_county_prefix THEN 1 ELSE 0 END) AS state_from_county_prefix_rows,
            COUNT(DISTINCT state_fips_2) FILTER (WHERE state_fips_2 IS NOT NULL) AS distinct_states_normalized,
            COUNT(DISTINCT county_fips_5) FILTER (WHERE county_fips_5 IS NOT NULL) AS distinct_counties_normalized
        FROM loan_years_geo
        GROUP BY activity_year
        ORDER BY activity_year;
        """,
    )
    for row in missing:
        for key, value in list(row.items()):
            if key != "activity_year":
                row[key] = fmt_int(value)

    examples = query_dicts(
        con,
        """
        SELECT
            activity_year,
            source_era,
            state_code,
            county_code,
            state_fips_2,
            state_fips_2_source,
            state_fips_2_from_county_prefix,
            county_fips_3,
            county_fips_5,
            county_fips_5_source,
            county_fips_5_valid_state_prefix,
            COUNT(*) AS row_count
        FROM loan_years_geo
        WHERE state_fips_2 IS NULL OR county_fips_5 IS NULL
        GROUP BY ALL
        ORDER BY row_count DESC
        LIMIT 30;
        """,
    )
    for row in examples:
        row["row_count"] = fmt_int(row["row_count"])

    sample_mappings = query_dicts(
        con,
        """
        SELECT
            activity_year,
            source_era,
            state_code,
            county_code,
            state_fips_2,
            state_fips_2_source,
            state_fips_2_from_county_prefix,
            county_fips_3,
            county_fips_5,
            county_fips_5_source,
            county_fips_5_valid_state_prefix,
            COUNT(*) AS row_count
        FROM loan_years_geo
        WHERE state_fips_2 IS NOT NULL AND county_fips_5 IS NOT NULL
        GROUP BY ALL
        ORDER BY activity_year, row_count DESC
        LIMIT 40;
        """,
    )
    for row in sample_mappings:
        row["row_count"] = fmt_int(row["row_count"])

    totals = query_dicts(
        con,
        """
        SELECT
            COUNT(*) AS row_count,
            SUM(CASE WHEN state_fips_2 IS NULL THEN 1 ELSE 0 END) AS missing_state_fips_2,
            SUM(CASE WHEN county_fips_5 IS NULL THEN 1 ELSE 0 END) AS missing_county_fips_5,
            SUM(CASE WHEN county_fips_5 IS NOT NULL AND state_fips_2 IS NULL THEN 1 ELSE 0 END) AS county_present_state_missing,
            SUM(
                CASE
                    WHEN county_fips_5 IS NOT NULL
                     AND state_fips_2 IS NOT NULL
                     AND SUBSTR(county_fips_5, 1, 2) <> state_fips_2
                    THEN 1
                    ELSE 0
                END
            ) AS state_county_prefix_mismatches,
            SUM(CASE WHEN state_fips_2_from_county_prefix THEN 1 ELSE 0 END) AS state_from_county_prefix_rows,
            COUNT(DISTINCT state_fips_2) FILTER (WHERE state_fips_2 IS NOT NULL) AS distinct_states_normalized,
            COUNT(DISTINCT county_fips_5) FILTER (WHERE county_fips_5 IS NOT NULL) AS distinct_counties_normalized
        FROM loan_years_geo;
        """,
    )[0]
    for key, value in list(totals.items()):
        totals[key] = fmt_int(value)

    source_flags = query_dicts(
        con,
        """
        SELECT
            activity_year,
            source_era,
            state_fips_2_source,
            county_fips_5_source,
            COUNT(*) AS row_count
        FROM loan_years_geo
        GROUP BY ALL
        ORDER BY activity_year, row_count DESC;
        """,
    )
    for row in source_flags:
        row["row_count"] = fmt_int(row["row_count"])

    objects = query_dicts(
        con,
        """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name IN ('state_fips_crosswalk', 'loan_years_geo')
        ORDER BY table_name;
        """,
    )
    return {
        "missing_by_year": missing,
        "unmapped_examples": examples,
        "sample_mappings": sample_mappings,
        "totals": totals,
        "source_flags": source_flags,
        "objects": objects,
    }


def build_markdown(current_formats: list[dict[str, Any]], validation: dict[str, Any]) -> str:
    lines = [
        "# Geography Normalization",
        "",
        "## Scope",
        "",
        "This step adds normalized geography fields to `data/duckdb/hmda_panel.duckdb`. It does not create final research aggregates, classify fintech lenders, delete raw files, or delete Parquet files.",
        "",
        "## Objects Created",
        "",
        markdown_table(validation["objects"], ["table_name", "table_type"]),
        "",
        "## Current Raw Geography Formats",
        "",
        markdown_table(
            current_formats,
            [
                "activity_year",
                "source_era",
                "row_count",
                "distinct_state_values",
                "distinct_county_values",
                "state_numeric_1_2",
                "state_alpha_2",
                "state_missing_or_na",
                "county_numeric_1_3",
                "county_numeric_5",
                "county_missing_or_na",
            ],
        ),
        "",
        "## Mapping Rules",
        "",
        "- If `state_code` is one or two numeric characters, left-pad it to two characters as `state_fips_2`.",
        "- If `state_code` is a two-letter abbreviation, map it through `state_fips_crosswalk`.",
        "- For post-2018 records with a valid five-digit `county_code`, derive `county_fips_5` directly from `county_code`.",
        "- For post-2018 records with a valid five-digit `county_code`, derive `state_fips_2` from the first two digits of `county_code` when `state_code` is missing, unmapped, or conflicts with the county prefix.",
        "- If `county_code` is one to three numeric characters, left-pad it to three characters as `county_fips_3` and combine with `state_fips_2` for `county_fips_5`.",
        "- A five-digit `county_code` is treated as valid for this pass when its first two digits match the internal state/territory FIPS crosswalk and its county suffix is not `000`.",
        "- Original `state_code` and `county_code` are preserved in `loan_years_geo`.",
        "- `state_fips_2_source`, `state_fips_2_from_county_prefix`, `county_fips_5_source`, and `county_fips_5_valid_state_prefix` document how normalized values were produced.",
        "",
        "## Validation Totals",
        "",
        markdown_table([validation["totals"]], list(validation["totals"].keys())),
        "",
        "## Validation By Year",
        "",
        markdown_table(
            validation["missing_by_year"],
            [
                "activity_year",
                "row_count",
                "missing_state_fips_2",
                "missing_county_fips_5",
                "county_present_state_missing",
                "state_county_prefix_mismatches",
                "state_from_county_prefix_rows",
                "distinct_states_normalized",
                "distinct_counties_normalized",
            ],
        ),
        "",
        "## Source Flag Counts",
        "",
        markdown_table(
            validation["source_flags"],
            [
                "activity_year",
                "source_era",
                "state_fips_2_source",
                "county_fips_5_source",
                "row_count",
            ],
        ),
        "",
        "## Examples Of Unmapped Records",
        "",
    ]
    if validation["unmapped_examples"]:
        lines.append(
            markdown_table(
                validation["unmapped_examples"],
                [
                    "activity_year",
                    "source_era",
                    "state_code",
                    "county_code",
                    "state_fips_2",
                    "state_fips_2_source",
                    "state_fips_2_from_county_prefix",
                    "county_fips_3",
                    "county_fips_5",
                    "county_fips_5_source",
                    "county_fips_5_valid_state_prefix",
                    "row_count",
                ],
            )
        )
    else:
        lines.append("No unmapped normalized state or county values found.")

    lines.extend(
        [
            "",
            "## Sample Successful Mappings",
            "",
            markdown_table(
                validation["sample_mappings"],
                [
                    "activity_year",
                    "source_era",
                    "state_code",
                    "county_code",
                    "state_fips_2",
                    "state_fips_2_source",
                    "state_fips_2_from_county_prefix",
                    "county_fips_3",
                    "county_fips_5",
                    "county_fips_5_source",
                    "county_fips_5_valid_state_prefix",
                    "row_count",
                ],
            ),
            "",
            "## Notes",
            "",
            "- `loan_years_geo` is a view over `loan_years`; it does not duplicate the loan-level dataset.",
            "- `state_fips_crosswalk` is an internal table containing US states, DC, and major territories present in HMDA-style data.",
            "- Post-2018 rows with valid five-digit county FIPS values use the county prefix as the fallback or conflict-resolution source for `state_fips_2`.",
            "- Remaining unmapped county records are primarily missing or `NA` county codes, plus records where the source county is not a usable FIPS component.",
            "- County-year research aggregates should use `state_fips_2` and `county_fips_5`, not the raw `state_code` and `county_code` fields.",
        ]
    )
    return "\n".join(lines) + "\n"


def normalize_geography() -> None:
    con = duckdb.connect(str(DB_PATH))
    try:
        current_formats = inspect_current_formats(con)
        create_crosswalk(con)
        create_normalized_view(con)
        validation = validate_normalization(con)
    finally:
        con.close()
    OUTPUT_PATH.write_text(build_markdown(current_formats, validation), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create normalized geography fields in the HMDA DuckDB database.")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without modifying the database.")
    args = parser.parse_args()
    if args.dry_run:
        print("CREATE OR REPLACE TABLE state_fips_crosswalk (...)")
        print(f"-- {len(STATE_CROSSWALK)} rows")
        print(CREATE_VIEW_SQL)
        return 0
    normalize_geography()
    print(f"updated {DB_PATH}")
    print(f"wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
