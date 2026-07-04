# HMDA County Panel

## Project Overview

This repository contains a reproducible HMDA mortgage-lending pipeline for 2007-2024. It builds county-year and lender-county-year panels from public HMDA loan-level data.

The purpose is to provide a data foundation for studying geographic expansion of mortgage lenders over time. Fintech classification is not included yet because the constructed canonical data does not contain lender names and no lender classification crosswalk has been added.

For the full research-methods memo, see [docs/final_summary.md](docs/final_summary.md).

## Final Outputs

| path | format | rows |
| --- | --- | ---: |
| `output/county_year_lending.csv` | CSV | 58,006 |
| `output/lender_county_year.parquet` | Parquet | 8,923,506 |
| `output/lender_county_year_sample.csv` | CSV | 100,000 |
| `output/export_manifest.csv` | CSV | 3 |
| `data/duckdb/hmda_panel.duckdb` | DuckDB database | n/a |

## Data Scale

- Loan-level rows processed: 312,095,276
- Years covered: 18, from 2007 through 2024
- County-year rows: 58,006
- Lender-county-year rows: 8,923,506
- Applications included in the county-year aggregate: 305,141,850
- Rows excluded due to missing geography: 6,953,426

## Pipeline Summary

```text
raw HMDA files -> annual Parquet -> DuckDB -> geography normalization -> aggregates -> exports
```

## Main Database Objects

- `loan_years`: canonical loan-level view over annual Parquet files.
- `loan_years_geo`: geography-normalized loan-level view with `state_fips_2` and `county_fips_5`.
- `county_year_lending`: county-year lending aggregate.
- `lender_county_year`: lender-county-year lending aggregate.
- `column_metadata`: metadata for canonical database columns.
- `year_summary`: year-level database summary table.
- QA tables: missing-geography and missing-lender tables for aggregate exclusions.

## Reproduction Commands

These are the current project commands. Large downloads and processing steps should be reviewed before running.

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-via-HMDA_USER_AGENT)"
python -m scripts.download --download --all-years --timeout-seconds 300 --retries 5 --backoff-seconds 10 --min-free-gb 100 --manifest data\raw\download_manifest.json
```

```powershell
python -m scripts.convert --all-years
```

```powershell
python -m scripts.build_db --all-years --force
```

```powershell
python -m scripts.normalize_geography
```

```powershell
python -m scripts.build_county_year_lending
```

```powershell
python -m scripts.research_readiness_audit
```

```powershell
python -m scripts.build_lender_county_year
```

```powershell
python -m scripts.export_tables
```

## Key Caveats

- HMDA has a major schema break in 2018.
- Pre-2018 lender IDs use `respondent_id`; post-2018 lender IDs use LEI.
- The canonical database has no lender names.
- Fintech classification requires external lender identity enrichment.
- Rows with missing county geography are excluded from the main county-level aggregates and preserved in QA tables.
- This run used a raw-first download approach. Future production runs should prefer year-at-a-time processing: download or stream one year, convert to Parquet, validate, and optionally remove the raw intermediate.

## Documentation Map

- [docs/final_summary.md](docs/final_summary.md): main research-methods and data-construction memo.
- [docs/db_qa.md](docs/db_qa.md): DuckDB QA results.
- [docs/geography_normalization.md](docs/geography_normalization.md): geography normalization rules and validation.
- [docs/county_year_lending.md](docs/county_year_lending.md): county-year aggregate documentation.
- [docs/lender_county_year.md](docs/lender_county_year.md): lender-county-year aggregate documentation.
- [docs/export_outputs.md](docs/export_outputs.md): exported file documentation.
- [docs/research_readiness_audit.md](docs/research_readiness_audit.md): readiness checks for lender-level and county-level analysis.
- [docs/schema_audit.md](docs/schema_audit.md): annual Parquet schema audit.
- [docs/plan.md](docs/plan.md): implementation plan.
- [docs/progress.md](docs/progress.md): project progress log.
