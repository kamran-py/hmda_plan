# HMDA County Panel

This repository contains a reproducible HMDA mortgage-lending data pipeline for 2007-2024. It builds county-year and lender-county-year panels from public HMDA loan-level data, with explicit handling of the 2018 HMDA schema break.

The project is a data-construction and research-readiness artifact. It is designed to make the data pipeline, assumptions, exclusions, and generated outputs legible to researchers, graduate faculty, and applied economics or finance professionals.

For the full research-methods memo, see [docs/final_summary.md](docs/final_summary.md).

## What This Repository Is

- A reproducible pipeline from public HMDA source files to analysis-ready county and lender-county panels.
- A documented approach to HMDA schema harmonization across 2007-2024.
- A large-scale DuckDB and Parquet workflow for data that is too large for ordinary in-memory processing.
- A foundation for later work on lender presence, geographic expansion, and fintech/nonbank mortgage lending.

## What This Repository Is Not

- It is not a final causal analysis.
- It does not classify lenders as fintech, nonbank, or bank.
- It does not resolve lender identities across the pre-2018 respondent ID system and the post-2018 LEI system.
- It does not commit the full raw HMDA files, annual Parquet intermediates, DuckDB database, or full lender-county-year Parquet export to GitHub.

## Data Scale

- Loan-level rows processed: 312,095,276.
- Years covered: 18, from 2007 through 2024.
- County-year rows: 58,006.
- Lender-county-year rows: 8,923,506.
- HMDA records included in the county-year aggregate: 305,141,850.
- Non-purchase application records included in the county-year aggregate: 259,119,806.
- Rows excluded due to missing geography: 6,953,426.

## Outputs

### Committed Small Outputs

These files are small enough to keep in GitHub and are available after cloning the repository.

| path | format | rows | purpose |
| --- | --- | ---: | --- |
| `output/county_year_lending.csv` | CSV | 58,006 | Main county-year panel for direct inspection and analysis; includes `state_name`, `total_records`, `application_records`, and `purchased_loans`. |
| `output/lender_county_year_sample.csv` | CSV | 100,000 | Year-stratified sample from the larger lender-county-year panel. |
| `output/export_manifest.csv` | CSV | 3 | Export audit trail with row counts and file sizes. |

### Generated Local Outputs

These artifacts are produced by the pipeline but are intentionally not committed to GitHub because of size, portability, or reproducibility concerns.

| path | format | rows | note |
| --- | --- | ---: | --- |
| `output/lender_county_year.parquet` | Parquet | 8,923,506 | Generated locally by `python -m scripts.export_tables`. |
| `data/duckdb/hmda_panel.duckdb` | DuckDB database | n/a | Generated locally by `python -m scripts.build_db --all-years --force` and later pipeline steps. |
| `data/raw/*` | ZIP/CSV | n/a | Raw HMDA source files; about 48 GiB in this run. |
| `data/parquet/*` | Parquet/JSON | 312,095,276 loan-level rows across annual files | Annual converted intermediates; about 6.82 GiB in this run. |

## Data Availability

The committed CSV outputs are included for quick review. The full lender-county-year table, DuckDB database, raw source files, and annual Parquet intermediates are generated local artifacts and are excluded by `.gitignore`.

This means a cloned copy of the repository can inspect the committed CSV outputs immediately, but cannot query the full DuckDB database or full lender-county-year Parquet export until the pipeline is rerun locally.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the lightweight tests:

```powershell
python -m unittest discover -s tests
```

## Quick Inspection

These commands work after cloning and do not require downloading the full HMDA source files.

```powershell
"output/county_year_lending.csv", "output/lender_county_year_sample.csv", "output/export_manifest.csv" |
    ForEach-Object {
        $rows = (Import-Csv $_ | Measure-Object).Count
        "{0}: {1:N0} rows" -f $_, $rows
    }
```

## Pipeline Summary

```text
public HMDA source files
-> cached raw files
-> annual Parquet files
-> canonical DuckDB view
-> geography-normalized view
-> county-year and lender-county-year aggregates
-> committed small CSV outputs and generated local large outputs
```

## Main Database Objects

The generated DuckDB database contains the following main objects after the full pipeline is run locally:

- `loan_years`: canonical loan-level view over annual Parquet files.
- `loan_years_geo`: geography-normalized loan-level view with `state_fips_2` and `county_fips_5`.
- `county_year_lending`: county-year lending aggregate.
- `lender_county_year`: lender-county-year lending aggregate.
- `column_metadata`: metadata for canonical database columns.
- `year_summary`: year-level database summary table.
- QA tables: missing-geography and missing-lender tables for aggregate exclusions.

## Reproduction Commands

Large downloads and processing steps should be reviewed before running. The raw source download requires substantial disk space.

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
- The canonical database has lender IDs but no lender names.
- Fintech classification requires external lender identity enrichment.
- `total_records` counts all HMDA records at the aggregate grain; `application_records` excludes purchased-loan records with `action_taken = '6'`.
- Rows with missing county geography are excluded from the main county-level aggregates and preserved in QA tables.
- The current output is a research data foundation, not a final causal estimate.
- This run used a raw-first download approach. Future production runs should prefer year-at-a-time processing: download or stream one year, convert to Parquet, validate, and optionally remove the raw intermediate.

## Data Sources

- Historic HMDA, 2007-2017:
  `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_{YEAR}_nationwide_all-records_codes.zip`
- HMDA Data Browser API, 2018-2024:
  `https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years={YEAR}`

## Documentation Map

- [docs/final_summary.md](docs/final_summary.md): main research-methods and data-construction memo.
- [docs/db_qa.md](docs/db_qa.md): DuckDB QA results.
- [docs/geography_normalization.md](docs/geography_normalization.md): geography normalization rules and validation.
- [docs/county_year_lending.md](docs/county_year_lending.md): county-year aggregate documentation.
- [docs/lender_county_year.md](docs/lender_county_year.md): lender-county-year aggregate documentation.
- [docs/export_outputs.md](docs/export_outputs.md): exported file documentation.
- [docs/committed_output_profile.md](docs/committed_output_profile.md): quick profile of the committed CSV outputs.
- [docs/research_readiness_audit.md](docs/research_readiness_audit.md): readiness checks for lender-level and county-level analysis.
- [docs/schema_audit.md](docs/schema_audit.md): annual Parquet schema audit.
- [docs/plan.md](docs/plan.md): implementation plan.
- [docs/development_log.md](docs/development_log.md): chronological development log. Early entries are historical and should not be read as the final project state.

## Reuse Note

The HMDA source data are public data distributed by CFPB/FFIEC. Repository users should review the upstream data documentation before publication or production use. Add an explicit repository license before inviting third-party code reuse.
