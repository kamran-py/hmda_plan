# Progress

## Current Status

- Repository inspected locally inside `C:\Users\kanop\hmda_plan`.
- Existing scaffold found:
  - `README.md`
  - `configs/smoke_test.example.json`
  - `docs/smoke-test-design.md`
  - `hmda_plan/`
  - `tests/`
- No parent directories were inspected.
- Phase 1 project rules were added in `AGENTS.md`.
- Large-data folders were created:
  - `data/raw`
  - `data/parquet`
  - `data/duckdb`
  - `output`
- Starter pipeline scripts were added under `scripts`.
- No network requests were made.
- No data was downloaded.
- No raw HMDA files were converted.
- No DuckDB database was built.

## Unresolved Questions

1. What lender classification source should define "fintech mortgage lender" over time?
2. Should fintech status be lender-year specific, lender-global, or based on origination channel?
3. Which county identifier should be canonical when older records have missing or suppressed county codes?
4. Should loan amounts be kept in original HMDA units or normalized to dollars across eras?
5. Which action-taken codes should count as applications, originations, denials, purchases, and withdrawals?
6. Should the panel include territories, missing county records, or only US counties with valid FIPS codes?
7. What metadata source should be used for official column descriptions and valid values?
8. What contact string should be used in the production User-Agent header?

## Next Phase Candidate

After approval, Phase 2 can run a two-year smoke test for `2007` and `2018` only. The exact download command should be reviewed and approved before any network request.

## Proposed Two-Year Validation Run

Status: prepared only. No network requests, downloads, conversions, or database builds have been run.

### Validation Years

- `2007`: pre-2018 historic HMDA format.
- `2018`: post-2018 HMDA Data Browser format.

### Source URLs

These URLs were verified by local template expansion only, not by making HTTP requests:

- `2007`: `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2007_nationwide_all-records_codes.zip`
- `2018`: `https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years=2018`

### Exact Download Commands Requiring Approval

Run these only after explicit approval:

```powershell
$UserAgent = "hmda-county-panel-research/0.1 (contact: set-before-download)"
if (Test-Path "data\raw\hmda_2007_nationwide.zip") { throw "Target already exists: data\raw\hmda_2007_nationwide.zip" }
curl.exe --location --fail --retry 3 --retry-delay 5 --continue-at - --user-agent $UserAgent --output "data\raw\hmda_2007_nationwide.zip.partial" "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2007_nationwide_all-records_codes.zip"
if ($LASTEXITCODE -eq 0) { Rename-Item -Path "data\raw\hmda_2007_nationwide.zip.partial" -NewName "hmda_2007_nationwide.zip" }
```

```powershell
$UserAgent = "hmda-county-panel-research/0.1 (contact: set-before-download)"
if (Test-Path "data\raw\hmda_2018_nationwide.csv") { throw "Target already exists: data\raw\hmda_2018_nationwide.csv" }
curl.exe --location --fail --retry 3 --retry-delay 5 --continue-at - --user-agent $UserAgent --output "data\raw\hmda_2018_nationwide.csv.partial" "https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years=2018"
if ($LASTEXITCODE -eq 0) { Rename-Item -Path "data\raw\hmda_2018_nationwide.csv.partial" -NewName "hmda_2018_nationwide.csv" }
```

Before approval, replace `contact: set-before-download` with the preferred contact string.

### Expected Raw Outputs

- `data/raw/hmda_2007_nationwide.zip`
- `data/raw/hmda_2018_nationwide.csv`

During interrupted downloads, temporary partial files may exist:

- `data/raw/hmda_2007_nationwide.zip.partial`
- `data/raw/hmda_2018_nationwide.csv.partial`

### Expected Converted Outputs

After a later approved conversion step:

- `data/parquet/hmda_2007.parquet`
- `data/parquet/hmda_2018.parquet`

The conversion should use DuckDB and Parquet, not pandas for the full raw files.

### Schema Difference Handling

The converter should map each era into canonical fields before writing Parquet:

- Historic `2007` fields:
  - `as_of_year` -> `activity_year`
  - `respondent_id` -> `lei_or_respondent_id`
  - `loan_amount_000s` -> `loan_amount`
  - `owner_occupancy` -> `occupancy_type`
- Post-2018 `2018` fields:
  - `activity_year` -> `activity_year`
  - `lei` -> `lei_or_respondent_id`
  - `loan_amount` -> `loan_amount`
  - `occupancy_type` -> `occupancy_type`

Shared fields such as `state_code`, `county_code`, `loan_type`, `loan_purpose`, `action_taken`, and `lien_status` should be preserved under canonical names. A `source_era` column should be added so downstream queries can distinguish old and new HMDA schema sources.

The `loan_amount` unit normalization is unresolved. Historic `loan_amount_000s` may need conversion to dollars or a clearly documented common unit before analysis.

### DuckDB Build Plan

After Parquet conversion is approved and completed, the pilot DuckDB database should be built from only:

- `data/parquet/hmda_2007.parquet`
- `data/parquet/hmda_2018.parquet`

Planned database:

- `data/duckdb/hmda_panel.duckdb`

Planned tables:

- `loan_years`: unioned canonical loan-level records from the two Parquet files.
- `column_metadata`: canonical column names, descriptions, DuckDB types, valid values, source-era mappings, and first/last available years.
- `county_year_lending`: county-year aggregates by `activity_year`, `state_code`, and `county_code`.

Initial aggregate fields:

- applications
- originations
- denials
- total loan amount
- average loan amount
- lender count

Fintech-specific aggregate fields should wait until the lender classification source is resolved.

## Lightweight URL Validation Step

Status: implemented but not run. This step makes network requests and requires approval before use.

The validation command checks only the two pilot URLs, `2007` and `2018`. It tries `HEAD` first. If a server reports that `HEAD` is unsupported, it falls back to a streaming `GET` with a `Range` header and reads only the first 1024 bytes before closing the connection.

The command reports:

- HTTP status
- method used (`HEAD` or fallback `GET`)
- final URL after redirects
- content type
- content length, if available
- fallback bytes read, if fallback `GET` is used

The User-Agent comes from the `HMDA_USER_AGENT` environment variable. If that variable is unset, the default is:

```text
hmda-county-panel-research/0.1 (contact: set-before-download)
```

Exact command requiring approval before any network request:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-before-download)"
python -m scripts.download --validate-urls --years 2007 2018
```

This command should not create files or download full HMDA datasets. It should only validate reachability and response headers for the two pilot URLs.

### URL Validation Result

Executed after user approval:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-before-download)"
python -m scripts.download --validate-urls --years 2007 2018
```

Result:

- `2007`: `HEAD` returned HTTP `403 Forbidden`; final URL remained `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2007_nationwide_all-records_codes.zip`; content type was `text/html`; content length was `479`.
- `2018`: `HEAD` returned HTTP `403 Forbidden`; final URL remained `https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years=2018`; content type was `text/html`; content length was `436`.

No files were created. No full HMDA files were downloaded.

Follow-up needed: decide whether the validator should treat `403` on `HEAD` as a signal to try the tiny fallback `GET`, since some public data servers block `HEAD` even when `GET` is allowed.

### Tiny Streaming GET Fallback

Status: implemented but not run.

The validator now treats these `HEAD` status codes as eligible for fallback:

- `400`
- `403`
- `405`
- `406`
- `501`

When fallback is used, it sends a `GET` request with:

- `Range: bytes=0-4095`
- `Accept-Encoding: identity`
- `Connection: close`

The validator reads only the first 4096 bytes and then closes the response. It does not create output files.

The fallback reports:

- HTTP status code
- final URL after redirects
- content type
- content length, if available
- number of fallback bytes read
- first bytes as hex
- first bytes as a short text preview
- a content check:
  - `zip_header_ok` or `zip_header_unexpected` for `.zip`
  - `text_csv_like`, `text_like`, or `text_csv_unexpected` for `.csv`

Exact command requiring approval before this network validation run:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-before-download)"
python -m scripts.download --validate-urls --years 2007 2018
```

### Tiny URL Validation Result

Executed after user approval:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: kamranahmed.8796@gmail.com)"
python -m scripts.download --validate-urls --years 2007 2018
```

Result:

- `2007`: `HEAD` returned HTTP `200`; final URL remained `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2007_nationwide_all-records_codes.zip`; content type was `application/zip`; content length was `461153015`; no bytes were read because `HEAD` succeeded; ZIP signature check was not needed.
- `2018`: `HEAD` fell back to tiny streaming `GET`; HTTP status was `206`; final URL was `https://files.ffiec.cfpb.gov/data-browser/datasets/2018/filtered-queries/three-year/1671077f106fda427706972aa37ff656.csv`; content type was `text/csv; charset=UTF-8`; content length was `4096`; bytes read was `4096`; first bytes hex were `61 63 74 69 76 69 74 79 5f 79 65 61 72 2c 6c 65`; text preview began with `activity_year,lei,derived_msa-md,state_code,county_code,census_tract,conforming_`; content check was `text_like`.

No raw HMDA files were created. No full HMDA files were downloaded.

## Full Raw Download Stage

Status: completed for raw files only.

Before running the full raw download, `scripts/download.py` was updated and locally checked for:

- year support for `2007` through `2024`
- historic source URLs for `2007-2017`
- Data Browser API source URLs for `2018-2024`
- raw output naming:
  - `data/raw/hmda_{YEAR}_nationwide.zip` for `2007-2017`
  - `data/raw/hmda_{YEAR}_nationwide.csv` for `2018-2024`
- resumable `.partial` downloads
- skip-existing behavior unless `--force` is passed
- retries with exponential backoff
- User-Agent from `HMDA_USER_AGENT`
- JSON manifest output at `data/raw/download_manifest.json`
- per-year progress output
- disk-space preflight

Local checks passed before download:

```powershell
python -B -m py_compile scripts\download.py scripts\config.py
python -B -m unittest discover -s tests
python -B -m scripts.download --all-years
```

Approved raw-download command executed:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: kamranahmed.8796@gmail.com)"
python -m scripts.download --download --all-years --timeout-seconds 300 --retries 5 --backoff-seconds 10 --min-free-gb 100 --manifest data\raw\download_manifest.json
```

Disk preflight reported `588.10 GiB` free in `data/raw` before starting.

Result:

- `18` records were written to `data/raw/download_manifest.json`.
- All `18` years have manifest status `downloaded`.
- Total downloaded raw bytes: `51723943287`.
- No historical ZIP files were unzipped.
- No CSV files were converted to Parquet.
- No DuckDB database was created.
- No aggregation was run.

Raw files created:

- `data/raw/hmda_2007_nationwide.zip`
- `data/raw/hmda_2008_nationwide.zip`
- `data/raw/hmda_2009_nationwide.zip`
- `data/raw/hmda_2010_nationwide.zip`
- `data/raw/hmda_2011_nationwide.zip`
- `data/raw/hmda_2012_nationwide.zip`
- `data/raw/hmda_2013_nationwide.zip`
- `data/raw/hmda_2014_nationwide.zip`
- `data/raw/hmda_2015_nationwide.zip`
- `data/raw/hmda_2016_nationwide.zip`
- `data/raw/hmda_2017_nationwide.zip`
- `data/raw/hmda_2018_nationwide.csv`
- `data/raw/hmda_2019_nationwide.csv`
- `data/raw/hmda_2020_nationwide.csv`
- `data/raw/hmda_2021_nationwide.csv`
- `data/raw/hmda_2022_nationwide.csv`
- `data/raw/hmda_2023_nationwide.csv`
- `data/raw/hmda_2024_nationwide.csv`

## Raw Download Audit

Status: completed. No unzip, conversion, DuckDB build, aggregation, or raw-file deletion was performed.

Manifest inspected:

- `data/raw/download_manifest.json`

Downloaded years:

- `2007-2024`

Manifest status summary:

- `downloaded`: `18`
- `failed`: `0`
- `skipped`: `0`
- errors: `0`

Partial download check:

- No `.partial` files remain in `data/raw`.

Raw disk usage:

- Total downloaded bytes: `51723943287`
- Total downloaded size: `48.172 GiB`

Files by year:

| Year | Status | Size | Output path |
|---:|---|---:|---|
| 2007 | downloaded | 0.429 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2007_nationwide.zip` |
| 2008 | downloaded | 0.288 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2008_nationwide.zip` |
| 2009 | downloaded | 0.309 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2009_nationwide.zip` |
| 2010 | downloaded | 0.343 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2010_nationwide.zip` |
| 2011 | downloaded | 0.312 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2011_nationwide.zip` |
| 2012 | downloaded | 0.405 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2012_nationwide.zip` |
| 2013 | downloaded | 0.373 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2013_nationwide.zip` |
| 2014 | downloaded | 0.501 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2014_nationwide.zip` |
| 2015 | downloaded | 0.314 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2015_nationwide.zip` |
| 2016 | downloaded | 0.358 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2016_nationwide.zip` |
| 2017 | downloaded | 0.170 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2017_nationwide.zip` |
| 2018 | downloaded | 5.475 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2018_nationwide.csv` |
| 2019 | downloaded | 6.367 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2019_nationwide.csv` |
| 2020 | downloaded | 9.093 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2020_nationwide.csv` |
| 2021 | downloaded | 9.322 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2021_nationwide.csv` |
| 2022 | downloaded | 5.698 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2022_nationwide.csv` |
| 2023 | downloaded | 4.098 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2023_nationwide.csv` |
| 2024 | downloaded | 4.318 GiB | `C:\Users\kanop\hmda_plan\data\raw\hmda_2024_nationwide.csv` |

HTTP status and redirect note:

- The current manifest records `source_url`, `content_length`, downloaded bytes, status, timestamps, and errors.
- It does not yet record per-download HTTP status code or final redirected URL.
- The download run reported no failed or unusual status during transfer.
- The earlier tiny URL validation observed that `2018` redirected from the Data Browser API URL to `files.ffiec.cfpb.gov`.

`.gitignore` audit:

- `data/raw/*`: excluded.
- `data/parquet/*`: excluded.
- `data/duckdb/*`: excluded.
- large generated files: `*.duckdb`, `*.duckdb.wal`, `*.parquet`, `*.csv`, `*.zip`, `*.tmp`, `*.partial` excluded.
- virtual environments: `.venv/` and `venv/` excluded.
- caches: `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` excluded.
- logs: `*.log` and `logs/` excluded.

## Raw-First Design Note

This run initially used a raw-first download approach. That approach is simple and reproducible because all annual source files are present in `data/raw` before conversion begins.

It is not ideal for large public datasets because it requires retaining large raw intermediates. The preferred production architecture is year-at-a-time:

```text
source file or stream -> convert to Parquet -> validate -> optionally delete raw intermediate
```

Since raw files are already downloaded, this run will use `data/raw` as a local source cache.

Future end-to-end runs should support `--keep-raw false` by default. Raw files should only be retained when explicitly requested.

Pipeline modes:

- `cached-raw mode`: use existing files in `data/raw` as source inputs.
- `year-at-a-time mode`: download or stream one year, convert to Parquet, validate, then optionally remove the raw intermediate.

## 2007/2018 Conversion Pilot Implementation

Status: implemented but not run. No Parquet conversion has been executed yet.

Scope:

- Convert only `2007` and `2018`.
- Use cached raw files from `data/raw`.
- Do not download anything.
- Do not delete raw files.
- Do not process `2008-2017` or `2019-2024`.
- Do not build DuckDB database tables yet.
- Do not run aggregation.

Raw input inspection:

- `2007`: `data/raw/hmda_2007_nationwide.zip`
  - ZIP contains one CSV member: `hmda_2007_nationwide_all-records_codes.csv`.
  - Member uncompressed size: `4549574602` bytes.
  - Header inspection found `45` columns.
  - Important old-format columns include `as_of_year`, `respondent_id`, `loan_type`, `loan_purpose`, `owner_occupancy`, `loan_amount_000s`, `action_taken`, `state_code`, `county_code`, and `lien_status`.
- `2018`: `data/raw/hmda_2018_nationwide.csv`
  - Header inspection found `99` columns.
  - Important post-2018 columns include `activity_year`, `lei`, `state_code`, `county_code`, `loan_type`, `loan_purpose`, `action_taken`, `loan_amount`, `occupancy_type`, and `lien_status`.

Implementation:

- `scripts/convert.py` now supports actual cached-raw conversion.
- The exact conversion command is:

```powershell
python -m scripts.convert --years 2007 2018
```

- Dry-run planning is available with:

```powershell
python -m scripts.convert --dry-run --years 2007 2018
```

Expected outputs after approved conversion:

- `data/parquet/hmda_2007.parquet`
- `data/parquet/hmda_2018.parquet`
- `data/parquet/conversion_metadata.json`

Temporary extraction behavior:

- DuckDB reads normal CSV paths. The 2007 input is a ZIP file, so the converter extracts its single CSV member to a temporary path under `data/raw/.convert_tmp/2007` during conversion.
- The temporary extracted CSV is removed after conversion unless `--keep-temp` is passed.
- The original ZIP file is not deleted or modified.

Output schema approach:

- Add canonical `activity_year`.
- Add `source_era` with values:
  - `pre_2018` for 2007
  - `post_2018` for 2018
- Add `lei_or_respondent_id`.
- Preserve raw input columns for debugging.
- If a raw column conflicts with a canonical column, it is retained with a `raw_` prefix. For example, 2018 raw `activity_year` becomes `raw_activity_year`.

Validation implemented:

- Row count must be greater than zero.
- Parquet output must exist.
- DuckDB must be able to query the Parquet output.
- `activity_year` must be present.
- Geography fields are checked using `state_code` and `county_code`.
- Lender identifier fields are checked using `respondent_id`, `lei`, or `lei_or_respondent_id`.

Conversion metadata records:

- year
- raw input path
- Parquet output path
- source era
- input columns
- output columns
- row count
- conversion status
- error, if any
- validation details
- ZIP member and temporary working path for ZIP-based years

Known schema issues:

- Historic `loan_amount_000s` is preserved but not yet normalized to post-2018 `loan_amount` units.
- Historic `respondent_id` and post-2018 `lei` are not equivalent identifiers; the canonical `lei_or_respondent_id` is useful for within-era analysis but needs care for cross-era lender matching.
- Older geographic fields may have missing, suppressed, or nonstandard county values; this pilot only checks that `state_code` and `county_code` fields exist.
- DuckDB is required for conversion. The local Python environment did not have the `duckdb` package installed when checked, so the conversion command will need DuckDB available before it can succeed.

Local checks completed without running conversion:

```powershell
python -B -m py_compile scripts\convert.py
python -B -m unittest discover -s tests
python -B -m scripts.convert --dry-run --years 2007 2018
```

### 2007/2018 Conversion Pilot Run Attempt

Status: attempted after user approval, failed before conversion because DuckDB is not installed in the local Python environment.

Approved command executed:

```powershell
python -m scripts.convert --years 2007 2018
```

Result:

- `2007`: failed with `DuckDB Python package is required: No module named 'duckdb'`.
- `2018`: failed with `DuckDB Python package is required: No module named 'duckdb'`.
- No Parquet files were created.
- No raw files were deleted.
- No additional years were processed.
- No final DuckDB database was built.
- No aggregation was run.

File state after failed attempt:

- `data/parquet/conversion_metadata.json` was written with failure records.
- `data/parquet/hmda_2007.parquet` does not exist.
- `data/parquet/hmda_2018.parquet` does not exist.

Next blocker:

- Install the DuckDB Python package, then rerun only the approved two-year conversion command.
- Installing DuckDB requires a network/package installation command and should be approved before running.

### DuckDB Installation

Executed after user provided the exact command:

```powershell
python -m pip install duckdb
```

Result:

- Installed `duckdb` version `1.5.4`.
- Verified with `python -c "import duckdb; print(duckdb.__version__)"`.
- Tests still pass with `python -B -m unittest discover -s tests`.

Conversion has not been rerun after installing DuckDB.

### 2007/2018 Conversion Pilot Completed

Executed after user provided the exact command:

```powershell
python -m scripts.convert --years 2007 2018
```

Initial result:

- Parquet files were written for both years.
- Validation initially reported `validation_failed` because the validation code read DuckDB `DESCRIBE` output incorrectly, using the type field instead of the column-name field.
- No raw files were deleted.
- No other years were processed.
- No final DuckDB database was built.
- No aggregation was run.

Fix applied:

- `scripts/convert.py` now reads column names correctly from DuckDB `DESCRIBE`.
- Added `--validate-existing` to refresh conversion metadata from existing Parquet files without reconverting or deleting outputs.

Metadata refresh command executed:

```powershell
python -m scripts.convert --validate-existing --years 2007 2018
```

Final validated outputs:

| Year | Status | Source era | Rows | Output columns | Parquet file |
|---:|---|---|---:|---:|---|
| 2007 | converted | pre_2018 | 26605695 | 48 | `data/parquet/hmda_2007.parquet` |
| 2018 | converted | post_2018 | 15140471 | 102 | `data/parquet/hmda_2018.parquet` |

Output files:

- `data/parquet/hmda_2007.parquet` (`230627970` bytes)
- `data/parquet/hmda_2018.parquet` (`558592156` bytes)
- `data/parquet/conversion_metadata.json`

Validation status:

- Row counts are greater than zero.
- Parquet files exist.
- DuckDB can query both Parquet files.
- `activity_year` is present.
- `state_code` and `county_code` are present.
- lender identifier fields are present through canonical `lei_or_respondent_id` and raw-era fields.

## Full Conversion Preparation

Status: prepared but not run.

`scripts/convert.py` was inspected and updated for full cached-raw conversion.

Confirmed behavior:

- Supports all years `2007-2024` with `--all-years`.
- Uses cached raw files in `data/raw`.
- Writes only Parquet outputs in `data/parquet`.
- Processes one year at a time.
- Skips existing valid Parquet files unless `--force` is passed.
- Can resume if interrupted: rerunning the same command skips completed Parquet files and continues remaining years.
- Writes/refreshes `data/parquet/conversion_metadata.json` after each year, not only at the end.
- Does not delete original raw files.
- For pre-2018 ZIP inputs, extracts the single CSV member to `data/raw/.convert_tmp/{year}` during conversion and removes that temporary extraction unless `--keep-temp` is passed.
- Does not build the final DuckDB database.
- Does not aggregate.

Local checks completed:

```powershell
python -B -m py_compile scripts\convert.py
python -B -m unittest discover -s tests
python -B -m scripts.convert --dry-run --all-years
```

Disk-space check:

- Free space on `C:`: `539.65 GiB`.

Rough output disk estimate based on pilot ratios:

- 2007 pre-2018 ratio: Parquet size / raw ZIP size = `0.5001`.
- 2018 post-2018 ratio: Parquet size / raw CSV size = `0.0950`.
- Estimated total Parquet size for `2007-2024`: `6.12 GiB`.
- Existing pilot Parquet outputs: `0.74 GiB`.
- Estimated remaining Parquet output to write: `5.38 GiB`.

Exact full-conversion command, not run:

```powershell
python -m scripts.convert --all-years
```

This command should skip existing `2007` and `2018` Parquet files, convert remaining cached raw years, and update `data/parquet/conversion_metadata.json` after each year.

## Full Parquet Conversion Completed

Status: completed for Parquet conversion only.

Approved command:

```powershell
python -m scripts.convert --all-years
```

Execution notes:

- The first long-running conversion process was interrupted by the tool timeout but continued in the background.
- It successfully skipped validated `2007` and `2018`, converted `2008-2017`, `2019-2022`, and then stalled while finalizing `2023`.
- The stale process was stopped and the same approved command was rerun.
- The rerun validated and skipped existing good Parquet files, then converted `2023` and `2024`.
- No raw files were deleted.
- No downloads were run.
- No final DuckDB database was built.
- No aggregation was run.

Final verification:

- `18` annual Parquet files exist in `data/parquet`.
- `data/parquet/conversion_metadata.json` has `18` records.
- Metadata errors: `0`.
- Total rows across annual Parquet files: `312095276`.
- Total Parquet size: `7328201304` bytes (`6.82 GiB`).
- No `scripts.convert` Python process remains running.
- No temporary extracted files remain under `data/raw/.convert_tmp`.

Final conversion metadata summary:

| Year | Metadata status | Source era | Rows |
|---:|---|---|---:|
| 2007 | skipped_existing | pre_2018 | 26605695 |
| 2008 | skipped_existing | pre_2018 | 17391570 |
| 2009 | skipped_existing | pre_2018 | 19493491 |
| 2010 | skipped_existing | pre_2018 | 16348557 |
| 2011 | skipped_existing | pre_2018 | 14873415 |
| 2012 | skipped_existing | pre_2018 | 18691551 |
| 2013 | skipped_existing | pre_2018 | 17016159 |
| 2014 | skipped_existing | pre_2018 | 12049341 |
| 2015 | skipped_existing | pre_2018 | 14374184 |
| 2016 | skipped_existing | pre_2018 | 16332987 |
| 2017 | skipped_existing | pre_2018 | 14285496 |
| 2018 | skipped_existing | post_2018 | 15140471 |
| 2019 | skipped_existing | post_2018 | 17573984 |
| 2020 | skipped_existing | post_2018 | 25699043 |
| 2021 | skipped_existing | post_2018 | 26269980 |
| 2022 | skipped_existing | post_2018 | 16125975 |
| 2023 | converted | post_2018 | 11564178 |
| 2024 | converted | post_2018 | 12259199 |

Note: `skipped_existing` means the rerun validated an already-created Parquet file and did not redo it.

## Parquet Schema Audit Completed

Status: completed. No DuckDB database was built, no aggregation was run, and no raw files were deleted.

Outputs:

- `docs/schema_audit.md`
- `data/parquet/schema_audit.json`

Audit method:

- Inspected `data/parquet/conversion_metadata.json`.
- Inspected all `18` annual Parquet schemas using DuckDB `DESCRIBE SELECT * FROM read_parquet(...)`.

Findings:

- Metadata records: `18`.
- Total rows represented in metadata: `312095276`.
- Columns common to all years: `14`.
- Columns only in pre-2018 years: `34`.
- Columns only in post-2018 years: `88`.
- Column type differences across same-named columns: none found.
- Lender-name fields: none found in the annual Parquet schemas.

Recommended first DuckDB build:

- Create a canonical loan-level view/table over the annual Parquet files.
- Normalize `loan_amount_000s` and `loan_amount` into a dollar-denominated canonical `loan_amount`.
- Normalize `owner_occupancy` and `occupancy_type` into canonical `occupancy_type`.
- Normalize `applicant_income_000s` and `income` only after confirming units.
- Keep raw source columns available during the first build for debugging schema differences.

## First DuckDB Build Completed

Status: completed. No final research aggregates were created, no raw files were deleted, and no downloads were run.

Implemented in:

- `scripts/build_db.py`

Exact command run:

```powershell
python -m scripts.build_db --all-years --force
```

Outputs:

- `data/duckdb/hmda_panel.duckdb`
- `data/duckdb/build_metadata.json`

DuckDB objects:

- `loan_years`: canonical view over annual Parquet files.
- `column_metadata`: metadata table with `14` canonical columns.
- `year_summary`: per-year summary table.
- `build_log`: key-value build log table.

`loan_years` columns:

- `activity_year`
- `source_era`
- `lender_id`
- `lender_id_type`
- `state_code`
- `county_code`
- `census_tract`
- `loan_amount`
- `loan_type`
- `loan_purpose`
- `occupancy_type`
- `action_taken`
- `applicant_income`
- `raw_source_columns`

Build verification:

- Database file size: `1060864` bytes.
- `year_summary` years: `18`.
- `year_summary` total rows: `312095276`.
- Min activity year: `2007`.
- Max activity year: `2024`.
- `column_metadata` rows: `14`.

Notes:

- `loan_years` is a view, so the database does not duplicate all loan-level rows.
- `loan_amount` multiplies historic `loan_amount_000s` by `1000` and casts post-2018 `loan_amount` directly.
- `raw_source_columns` stores selected source fields used for canonical mappings, not the full raw source record.
