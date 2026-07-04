from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from scripts.normalize_geography import STATE_CROSSWALK


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hmda_panel.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "output"
MANIFEST_PATH = OUTPUT_DIR / "export_manifest.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "export_outputs.md"

COUNTY_TABLE = "county_year_lending"
LENDER_TABLE = "lender_county_year"
LENDER_SAMPLE_ROWS = 100_000

COUNTY_CSV_PATH = OUTPUT_DIR / "county_year_lending.csv"
LENDER_PARQUET_PATH = OUTPUT_DIR / "lender_county_year.parquet"
LENDER_SAMPLE_CSV_PATH = OUTPUT_DIR / "lender_county_year_sample.csv"
LENDER_CSV_GZ_PATH = OUTPUT_DIR / "lender_county_year.csv.gz"


def state_name_case_sql(column_name: str = "state_fips_2") -> str:
    case_lines = []
    for state_fips, _state_abbr, state_name in STATE_CROSSWALK:
        escaped_state_name = state_name.replace("'", "''")
        case_lines.append(f"            WHEN {column_name} = '{state_fips}' THEN '{escaped_state_name}'")
    cases = "\n".join(case_lines)
    return f"CASE\n{cases}\n            ELSE NULL\n        END"


def sql_literal(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def repo_relative_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def query_one(con: duckdb.DuckDBPyConnection, sql: str) -> Any:
    return con.execute(sql).fetchone()[0]


def copy_to_csv(
    con: duckdb.DuckDBPyConnection,
    query: str,
    output_path: Path,
    compression: str | None = None,
) -> None:
    compression_clause = f", COMPRESSION '{compression}'" if compression else ""
    con.execute(
        f"""
        COPY (
            {query}
        )
        TO {sql_literal(output_path)}
        WITH (HEADER, DELIMITER ',', QUOTE '"', ESCAPE '"'{compression_clause});
        """
    )


def copy_to_parquet(con: duckdb.DuckDBPyConnection, query: str, output_path: Path) -> None:
    con.execute(
        f"""
        COPY (
            {query}
        )
        TO {sql_literal(output_path)}
        WITH (FORMAT PARQUET, COMPRESSION ZSTD);
        """
    )


def export_output(
    con: duckdb.DuckDBPyConnection,
    label: str,
    table_name: str,
    output_path: Path,
    query: str,
    row_count: int,
    force: bool,
    output_format: str,
    compression: str = "",
) -> dict[str, Any]:
    if output_path.exists() and not force:
        return {
            "label": label,
            "table_name": table_name,
            "output_path": repo_relative_path(output_path),
            "format": output_format,
            "compression": compression,
            "status": "skipped_existing",
            "row_count": row_count,
            "file_size_bytes": output_path.stat().st_size,
            "started_at": "",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": "",
        }

    started_at = datetime.now(timezone.utc).isoformat()
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_format == "csv":
            copy_to_csv(con, query, output_path)
        elif output_format == "csv.gz":
            copy_to_csv(con, query, output_path, compression="gzip")
        elif output_format == "parquet":
            copy_to_parquet(con, query, output_path)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        return {
            "label": label,
            "table_name": table_name,
            "output_path": repo_relative_path(output_path),
            "format": output_format,
            "compression": compression,
            "status": "exported",
            "row_count": row_count,
            "file_size_bytes": output_path.stat().st_size,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": "",
        }
    except Exception as exc:
        return {
            "label": label,
            "table_name": table_name,
            "output_path": repo_relative_path(output_path),
            "format": output_format,
            "compression": compression,
            "status": "failed",
            "row_count": "",
            "file_size_bytes": "",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }


def write_manifest(records: list[dict[str, Any]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "label",
        "table_name",
        "output_path",
        "format",
        "compression",
        "status",
        "row_count",
        "file_size_bytes",
        "started_at",
        "finished_at",
        "error",
    ]
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def fmt_int(value: Any) -> str:
    if value in ("", None):
        return ""
    return f"{int(value):,}"


def write_docs(records: list[dict[str, Any]], row_counts: dict[str, int], include_large_csv: bool) -> None:
    doc_records: list[dict[str, Any]] = []
    for record in records:
        doc_records.append(
            {
                "file": Path(record["output_path"]).name,
                "table": record["table_name"],
                "format": record["format"],
                "rows": fmt_int(record["row_count"]),
                "size_bytes": fmt_int(record["file_size_bytes"]),
                "status": record["status"],
            }
        )
    lines = [
        "# Export Outputs",
        "",
        "## Scope",
        "",
        "This export step creates researcher-facing files from existing DuckDB tables. It does not download data, delete raw or Parquet files, classify fintech lenders, or rebuild the database.",
        "",
        "The small CSV outputs and manifest are committed for public review. The full lender-county-year Parquet export is generated locally and is not committed to GitHub.",
        "",
        "## Source Row Counts",
        "",
        markdown_table(
            [
                {"table": COUNTY_TABLE, "row_count": fmt_int(row_counts[COUNTY_TABLE])},
                {"table": LENDER_TABLE, "row_count": fmt_int(row_counts[LENDER_TABLE])},
            ],
            ["table", "row_count"],
        ),
        "",
        "## Exported Files",
        "",
        markdown_table(doc_records, ["file", "table", "format", "rows", "size_bytes", "status"]),
        "",
        "## Large Table Format",
        "",
        "`lender_county_year` is exported as Parquet by default because it has millions of rows. Parquet is smaller, typed, faster to read with DuckDB, R, Python, and other analytics tools, and avoids the large disk footprint and slower parsing of a raw CSV.",
        "",
        "A 100,000-row CSV sample is exported for quick inspection in spreadsheet tools. The sample is stratified by `activity_year` so the public sample is not limited to the first year in sort order.",
        "",
        "Default exports include `state_name` alongside `state_fips_2`. County names require a county FIPS reference table and are intentionally not inferred from the five-digit FIPS code alone.",
        "",
        "## Full CSV Option",
        "",
        "To create a full compressed CSV later, run:",
        "",
        "```powershell",
        "python -m scripts.export_tables --include-large-csv",
        "```",
        "",
        "That optional command writes `output/lender_county_year.csv.gz` in addition to the default outputs.",
        "",
        f"Full compressed CSV included in this run: `{include_large_csv}`",
    ]
    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def planned_exports(include_large_csv: bool) -> list[tuple[str, str, Path, str, str]]:
    state_name_expr = state_name_case_sql("state_fips_2")
    county_query = f"""
SELECT
    activity_year,
    state_fips_2,
    {state_name_expr} AS state_name,
    county_fips_5,
    * EXCLUDE (activity_year, state_fips_2, county_fips_5)
FROM {COUNTY_TABLE}
ORDER BY activity_year, state_fips_2, county_fips_5
""".strip()
    lender_query = f"""
SELECT
    activity_year,
    state_fips_2,
    {state_name_expr} AS state_name,
    county_fips_5,
    lender_id,
    * EXCLUDE (activity_year, state_fips_2, county_fips_5, lender_id)
FROM {LENDER_TABLE}
ORDER BY activity_year, state_fips_2, county_fips_5, lender_id
""".strip()
    lender_sample_query = f"""
SELECT * EXCLUDE (sample_rank, sample_rows_per_year)
FROM (
    SELECT
        activity_year,
        state_fips_2,
        {state_name_expr} AS state_name,
        county_fips_5,
        lender_id,
        * EXCLUDE (activity_year, state_fips_2, county_fips_5, lender_id),
        ROW_NUMBER() OVER (
            PARTITION BY activity_year
            ORDER BY state_fips_2, county_fips_5, lender_id
        ) AS sample_rank,
        CEIL({LENDER_SAMPLE_ROWS}::DOUBLE / COUNT(DISTINCT activity_year) OVER ()) AS sample_rows_per_year
    FROM {LENDER_TABLE}
)
WHERE sample_rank <= sample_rows_per_year
ORDER BY activity_year, state_fips_2, county_fips_5, lender_id
LIMIT {LENDER_SAMPLE_ROWS}
""".strip()
    exports = [
        (
            "county_year_lending_csv",
            COUNTY_TABLE,
            COUNTY_CSV_PATH,
            county_query,
            "csv",
        ),
        (
            "lender_county_year_parquet",
            LENDER_TABLE,
            LENDER_PARQUET_PATH,
            lender_query,
            "parquet",
        ),
        (
            "lender_county_year_sample_csv",
            LENDER_TABLE,
            LENDER_SAMPLE_CSV_PATH,
            lender_sample_query,
            "csv",
        ),
    ]
    if include_large_csv:
        exports.append(
            (
                "lender_county_year_csv_gz",
                LENDER_TABLE,
                LENDER_CSV_GZ_PATH,
                lender_query,
                "csv.gz",
            )
        )
    return exports


def main() -> int:
    parser = argparse.ArgumentParser(description="Export approved HMDA DuckDB tables.")
    parser.add_argument("--include-large-csv", action="store_true", help="Also export lender_county_year as gzip CSV.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing CSV outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned exports without creating files.")
    args = parser.parse_args()

    exports = planned_exports(args.include_large_csv)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        row_counts = {
            COUNTY_TABLE: int(query_one(con, f"SELECT COUNT(*) FROM {COUNTY_TABLE}")),
            LENDER_TABLE: int(query_one(con, f"SELECT COUNT(*) FROM {LENDER_TABLE}")),
        }
    finally:
        con.close()

    if args.dry_run:
        print("row_counts")
        for table_name, row_count in row_counts.items():
            print(f"{table_name}: {row_count}")
        print("planned_exports")
        for label, table_name, output_path, _query, output_format in exports:
            print(f"{label}: {table_name} -> {output_path} ({output_format})")
        print(f"manifest -> {MANIFEST_PATH}")
        print(f"docs -> {DOC_PATH}")
        return 0

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        records = [
            export_output(
                con=con,
                label=label,
                table_name=table_name,
                output_path=output_path,
                query=query,
                row_count=min(row_counts[table_name], LENDER_SAMPLE_ROWS)
                if label == "lender_county_year_sample_csv"
                else row_counts[table_name],
                force=args.force,
                output_format=output_format,
                compression="gzip" if output_format == "csv.gz" else "",
            )
            for label, table_name, output_path, query, output_format in exports
        ]
    finally:
        con.close()

    write_manifest(records)
    write_docs(records, row_counts, args.include_large_csv)
    for record in records:
        print(
            f"{record['status']} {record['label']} table={record['table_name']} "
            f"format={record['format']} rows={record['row_count']} "
            f"bytes={record['file_size_bytes']} path={record['output_path']}"
        )
    print(f"wrote {MANIFEST_PATH}")
    print(f"wrote {DOC_PATH}")

    failed = [record for record in records if record["status"] == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
