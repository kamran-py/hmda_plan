# HMDA County Panel

Reproducible HMDA mortgage-lending pipeline for 2007–2024. It builds county-year
and lender-county-year panels from public loan-level data, including the 2018 schema break.

It documents the pipeline, assumptions, exclusions, and outputs for research use.

For the full research-methods memo, see [docs/final_summary.md](docs/final_summary.md).

## Scope

- Reproducible public-HMDA pipeline with documented cross-era harmonization.
- DuckDB/Parquet workflow for large source files.
- Foundation for later lender-presence, geographic-expansion, and fintech/nonbank research.
- Not a causal analysis; lender identity and fintech/nonbank classification remain out of scope.
- Raw files, annual Parquet intermediates, the DuckDB database, and the full lender-county-year export are not committed.

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

Available after cloning:

| path | format | rows | purpose |
| --- | --- | ---: | --- |
| `output/county_year_lending.csv` | CSV | 58,006 | Main county-year panel for direct inspection and analysis; includes `state_name`, `total_records`, `application_records`, and `purchased_loans`. |
| `output/lender_county_year_sample.csv` | CSV | 100,000 | Year-stratified sample from the larger lender-county-year panel. |
| `output/export_manifest.csv` | CSV | 3 | Export audit trail with row counts and file sizes. |

### Generated Local Outputs

Generated locally and excluded from GitHub:

| path | format | rows | note |
| --- | --- | ---: | --- |
| `output/lender_county_year.parquet` | Parquet | 8,923,506 | Generated locally by `python -m scripts.export_tables`. |
| `data/duckdb/hmda_panel.duckdb` | DuckDB database | n/a | Generated locally by `python -m scripts.build_db --all-years --force` and later pipeline steps. |
| `data/raw/*` | ZIP/CSV | n/a | Raw HMDA source files; about 48 GiB in this run. |
| `data/parquet/*` | Parquet/JSON | 312,095,276 loan-level rows across annual files | Annual converted intermediates; about 6.82 GiB in this run. |

## Data Availability

Committed CSVs are ready to inspect. The full lender-county-year table, DuckDB
database, raw sources, and annual Parquet intermediates are local artifacts;
rerun the pipeline to create them.

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

Works after cloning without downloading the full source files:

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

After a full local run, the DuckDB database contains:

- `loan_years`: canonical loan-level view over annual Parquet files.
- `loan_years_geo`: geography-normalized loan-level view with `state_fips_2` and `county_fips_5`.
- `county_year_lending`: county-year lending aggregate.
- `lender_county_year`: lender-county-year lending aggregate.
- `column_metadata`: metadata for canonical database columns.
- `year_summary`: year-level database summary table.
- QA tables for missing geography and lender values.

## Reproduction Commands

Review large downloads before running; raw sources require substantial disk space.

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
- The canonical database has lender IDs, not names; fintech classification needs external enrichment.
- `total_records` counts all HMDA records at the aggregate grain; `application_records` excludes purchased-loan records with `action_taken = '6'`.
- Rows with missing county geography are excluded from the main county-level aggregates and preserved in QA tables.
- This is a research-data foundation, not a causal estimate.
- Future production runs should prefer year-at-a-time processing.

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
- [docs/development_log.md](docs/development_log.md): chronological log; early entries are historical.

## Reuse Note

HMDA data are public CFPB/FFIEC data. Review upstream documentation before
publication or production use. Add a license before inviting third-party reuse.
