from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARQUET_DIR = PROJECT_ROOT / "data" / "parquet"
METADATA_PATH = PARQUET_DIR / "conversion_metadata.json"
JSON_OUTPUT_PATH = PARQUET_DIR / "schema_audit.json"
MD_OUTPUT_PATH = PROJECT_ROOT / "docs" / "schema_audit.md"

PRE_YEARS = tuple(range(2007, 2018))
POST_YEARS = tuple(range(2018, 2025))
ALL_YEARS = PRE_YEARS + POST_YEARS

KEY_FIELD_CANDIDATES = {
    "activity_year": ["activity_year", "raw_activity_year", "as_of_year"],
    "state_code": ["state_code"],
    "county_code": ["county_code"],
    "census_tract": ["census_tract", "census_tract_number"],
    "lei_or_respondent_id": ["lei_or_respondent_id", "lei", "respondent_id"],
    "lender_name_fields": [
        "respondent_name",
        "institution_name",
        "lender_name",
        "legal_entity_name",
    ],
    "loan_amount": ["loan_amount", "loan_amount_000s"],
    "loan_type": ["loan_type"],
    "loan_purpose": ["loan_purpose"],
    "occupancy_type": ["occupancy_type", "owner_occupancy"],
    "action_taken": ["action_taken"],
    "applicant_income": ["income", "applicant_income_000s"],
    "race_fields": [
        "derived_race",
        "applicant_race_1",
        "applicant_race_2",
        "applicant_race_3",
        "applicant_race_4",
        "applicant_race_5",
        "co_applicant_race_1",
        "co_applicant_race_2",
        "co_applicant_race_3",
        "co_applicant_race_4",
        "co_applicant_race_5",
        "applicant_race-1",
        "applicant_race-2",
        "applicant_race-3",
        "applicant_race-4",
        "applicant_race-5",
        "co-applicant_race-1",
        "co-applicant_race-2",
        "co-applicant_race-3",
        "co-applicant_race-4",
        "co-applicant_race-5",
    ],
}

CANONICAL_SCHEMA = [
    {
        "name": "activity_year",
        "type": "INTEGER",
        "source": "activity_year",
        "note": "Already canonical in all converted Parquet files.",
    },
    {
        "name": "source_era",
        "type": "VARCHAR",
        "source": "source_era",
        "note": "pre_2018 for 2007-2017 and post_2018 for 2018-2024.",
    },
    {
        "name": "lender_id",
        "type": "VARCHAR",
        "source": "lei_or_respondent_id",
        "note": "Historic respondent_id and post-2018 LEI are not equivalent ID systems.",
    },
    {
        "name": "lender_id_type",
        "type": "VARCHAR",
        "source": "derived from source_era",
        "note": "Use respondent_id for pre_2018 and lei for post_2018.",
    },
    {
        "name": "state_code",
        "type": "VARCHAR",
        "source": "state_code",
        "note": "Preserve leading zeros.",
    },
    {
        "name": "county_code",
        "type": "VARCHAR",
        "source": "county_code",
        "note": "Preserve leading zeros and missing/suppressed codes.",
    },
    {
        "name": "census_tract",
        "type": "VARCHAR",
        "source": "census_tract_number for pre_2018; census_tract for post_2018",
        "note": "Keep as text because formats differ across eras.",
    },
    {
        "name": "loan_amount",
        "type": "DOUBLE",
        "source": "loan_amount_000s for pre_2018; loan_amount for post_2018",
        "note": "For comparable dollars, multiply historic loan_amount_000s by 1000.",
    },
    {
        "name": "loan_type",
        "type": "VARCHAR",
        "source": "loan_type",
        "note": "Code meanings should be documented in metadata tables.",
    },
    {
        "name": "loan_purpose",
        "type": "VARCHAR",
        "source": "loan_purpose",
        "note": "Code meanings changed across HMDA eras and need metadata.",
    },
    {
        "name": "occupancy_type",
        "type": "VARCHAR",
        "source": "owner_occupancy for pre_2018; occupancy_type for post_2018",
        "note": "Era-specific code values need metadata.",
    },
    {
        "name": "action_taken",
        "type": "VARCHAR",
        "source": "action_taken",
        "note": "Use coded values for aggregation definitions.",
    },
    {
        "name": "applicant_income",
        "type": "DOUBLE",
        "source": "applicant_income_000s for pre_2018; income for post_2018",
        "note": "Confirm units before analysis; historic field is explicitly in thousands.",
    },
    {
        "name": "raw_source_columns",
        "type": "STRUCT or retained wide columns",
        "source": "era-specific raw columns",
        "note": "Retain raw fields during initial DuckDB build for debugging schema differences.",
    },
]


def parquet_path(year: int) -> Path:
    return PARQUET_DIR / f"hmda_{year}.parquet"


def inspect_schema(con: duckdb.DuckDBPyConnection, year: int) -> list[dict[str, str]]:
    path = str(parquet_path(year)).replace("\\", "/")
    rows = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchall()
    return [
        {
            "column_name": row[0],
            "column_type": row[1],
            "nullable": row[2],
        }
        for row in rows
    ]


def years_for_column(schema_by_year: dict[int, list[dict[str, str]]], column: str) -> list[int]:
    return [
        year
        for year, schema in schema_by_year.items()
        if column in {entry["column_name"] for entry in schema}
    ]


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def build_audit() -> dict[str, object]:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    con = duckdb.connect(database=":memory:")
    schema_by_year = {year: inspect_schema(con, year) for year in ALL_YEARS}
    columns_by_year = {
        year: {entry["column_name"] for entry in schema}
        for year, schema in schema_by_year.items()
    }
    types_by_column: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for year, schema in schema_by_year.items():
        for entry in schema:
            types_by_column[entry["column_name"]][entry["column_type"]].append(year)

    all_column_sets = list(columns_by_year.values())
    common_columns = sorted(set.intersection(*all_column_sets))
    pre_columns = set.union(*(columns_by_year[year] for year in PRE_YEARS))
    post_columns = set.union(*(columns_by_year[year] for year in POST_YEARS))
    only_pre = sorted(pre_columns - post_columns)
    only_post = sorted(post_columns - pre_columns)
    type_differences = {
        column: dict(type_map)
        for column, type_map in sorted(types_by_column.items())
        if len(type_map) > 1
    }

    key_field_availability = {}
    for logical_name, candidates in KEY_FIELD_CANDIDATES.items():
        by_year = {}
        for year, year_columns in columns_by_year.items():
            present = [column for column in candidates if column in year_columns]
            by_year[str(year)] = {
                "present": bool(present),
                "columns": present,
            }
        key_field_availability[logical_name] = {
            "candidate_columns": candidates,
            "by_year": by_year,
        }

    return {
        "metadata_summary": {
            "metadata_path": str(METADATA_PATH.relative_to(PROJECT_ROOT)),
            "records": len(metadata),
            "years": [record["year"] for record in metadata],
            "total_rows": sum(record["row_count"] or 0 for record in metadata),
            "statuses": sorted({record["conversion_status"] for record in metadata}),
            "errors": [
                {"year": record["year"], "error": record["error"]}
                for record in metadata
                if record.get("error")
            ],
        },
        "schema_by_year": schema_by_year,
        "column_counts_by_year": {
            str(year): len(schema)
            for year, schema in schema_by_year.items()
        },
        "common_columns_all_years": common_columns,
        "pre_2018_only_columns": only_pre,
        "post_2018_only_columns": only_post,
        "column_type_differences": type_differences,
        "key_field_availability": key_field_availability,
        "recommended_canonical_schema": CANONICAL_SCHEMA,
    }


def build_markdown(audit: dict[str, object]) -> str:
    metadata = audit["metadata_summary"]
    key_availability = audit["key_field_availability"]
    common = audit["common_columns_all_years"]
    only_pre = audit["pre_2018_only_columns"]
    only_post = audit["post_2018_only_columns"]
    type_diffs = audit["column_type_differences"]

    key_rows = []
    for field, detail in key_availability.items():
        years_present = [
            year
            for year, value in detail["by_year"].items()
            if value["present"]
        ]
        columns = sorted({
            column
            for value in detail["by_year"].values()
            for column in value["columns"]
        })
        key_rows.append(
            [
                field,
                ", ".join(columns) if columns else "none found",
                f"{years_present[0]}-{years_present[-1]}" if len(years_present) == len(ALL_YEARS) else ", ".join(years_present) if years_present else "none",
            ]
        )

    canonical_rows = [
        [item["name"], item["type"], item["source"], item["note"]]
        for item in audit["recommended_canonical_schema"]
    ]

    lines = [
        "# HMDA Parquet Schema Audit",
        "",
        "## Scope",
        "",
        "This audit inspects the 18 annual Parquet files in `data/parquet` using DuckDB metadata queries. It does not build a DuckDB database, aggregate data, delete raw files, or modify raw inputs.",
        "",
        "## Metadata Summary",
        "",
        f"- Metadata file: `{metadata['metadata_path']}`",
        f"- Metadata records: `{metadata['records']}`",
        f"- Years covered: `{metadata['years'][0]}-{metadata['years'][-1]}`",
        f"- Total rows: `{metadata['total_rows']}`",
        f"- Conversion statuses present: `{', '.join(metadata['statuses'])}`",
        f"- Metadata errors: `{len(metadata['errors'])}`",
        "",
        "## Column Counts",
        "",
        markdown_table(
            ["Year", "Columns"],
            [[year, count] for year, count in audit["column_counts_by_year"].items()],
        ),
        "",
        "## Columns Common To All Years",
        "",
        ", ".join(f"`{column}`" for column in common),
        "",
        "## Columns Only In Pre-2018 Years",
        "",
        ", ".join(f"`{column}`" for column in only_pre),
        "",
        "## Columns Only In Post-2018 Years",
        "",
        ", ".join(f"`{column}`" for column in only_post),
        "",
        "## Column Type Differences Across Years",
        "",
    ]

    if type_diffs:
        diff_rows = [
            [column, "; ".join(f"{dtype}: {years}" for dtype, years in type_map.items())]
            for column, type_map in type_diffs.items()
        ]
        lines.append(markdown_table(["Column", "Types by year"], diff_rows))
    else:
        lines.append("No column type differences were found for columns sharing the same name across years.")

    lines.extend(
        [
            "",
            "## Key Field Availability",
            "",
            markdown_table(["Logical field", "Observed columns", "Years present"], key_rows),
            "",
            "## Recommended Canonical Schema For First DuckDB Build",
            "",
            markdown_table(["Column", "Type", "Source", "Note"], canonical_rows),
            "",
            "## Notes",
            "",
            "- `activity_year`, `source_era`, `lei_or_respondent_id`, `state_code`, `county_code`, `loan_type`, `loan_purpose`, and `action_taken` are already common across all years.",
            "- Historic `loan_amount_000s` and post-2018 `loan_amount` should be normalized into a canonical dollar-denominated `loan_amount` field before cross-era analysis.",
            "- Historic `owner_occupancy` and post-2018 `occupancy_type` should be mapped into canonical `occupancy_type`.",
            "- Historic `applicant_income_000s` and post-2018 `income` should be mapped carefully after confirming units.",
            "- No lender-name field is present in these Parquet schemas; lender classification will need an external lender crosswalk or metadata source.",
            "- Race fields are era-specific and should remain available as raw columns while canonical race/ethnicity handling is designed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    audit = build_audit()
    JSON_OUTPUT_PATH.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    MD_OUTPUT_PATH.write_text(build_markdown(audit), encoding="utf-8")
    print(f"wrote {JSON_OUTPUT_PATH}")
    print(f"wrote {MD_OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
