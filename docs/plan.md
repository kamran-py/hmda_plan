# Implementation Plan

## Goal

Build a county-level and lender-county-level panel dataset of US mortgage lending from HMDA loan-level data for 2007-2024, suitable for later research on geographic expansion by mortgage lenders.

## Data Sources

- `2007-2017`: CFPB historic HMDA zipped CSV files with numeric codes and older LAR column names.
- `2018-2024`: FFIEC/CFPB Data Browser API CSV streams with the post-2018 HMDA schema.

## Processing Strategy

Use a staged workflow:

1. Download each source file to `data/raw`.
2. Convert each annual raw CSV to annual Parquet in `data/parquet`.
3. Normalize schema differences into a canonical loan-level view.
4. Build a DuckDB database in `data/duckdb`.
5. Create metadata tables for columns, descriptions, types, valid values, source era, and year availability.
6. Build county-year aggregate tables in DuckDB.
7. Export final county-level panel outputs to `output`.

Pandas should not be used for full raw files. Use DuckDB CSV readers, streaming file operations, and Parquet outputs.

## Pipeline Modes

### cached-raw mode

Use existing files in `data/raw` as source inputs. This is the mode for the current run because the full raw files have already been downloaded and can serve as a local source cache.

### year-at-a-time mode

Download or stream one year, convert it to Parquet, validate the Parquet output, then optionally remove the raw intermediate. This is the preferred production architecture for large public datasets because it limits peak disk usage and avoids retaining large raw files unless needed.

Future end-to-end runs should support `--keep-raw false` by default. Raw files should only be retained when explicitly requested.

## Raw-First Design Note

This project initially used a raw-first download approach: all annual source files were downloaded into `data/raw` before conversion. This is simple and reproducible, and it makes retrying conversion easier because the network source is no longer involved.

That approach is not ideal for large public datasets. It increases local disk requirements and keeps large intermediate files longer than necessary. The preferred production architecture is year-at-a-time:

```text
source file or stream -> convert to Parquet -> validate -> optionally delete raw intermediate
```

Since raw files are already downloaded for this run, conversion should use `data/raw` as a local source cache. Later production runs should default to removing raw intermediates unless `--keep-raw` is explicitly enabled.

## Smoke-Test Design

The initial smoke test should use only:

- `2007`: validates the historic pre-2018 format.
- `2018`: validates the post-2018 format.

The smoke test should eventually:

- Download only the two approved smoke-test years after explicit approval.
- Resume interrupted downloads.
- Send a clear User-Agent header.
- Convert only the two smoke-test files to Parquet.
- Verify canonical column mapping for both schema eras.
- Build a small DuckDB database with metadata and county-year aggregates.

The first validation pass should avoid downloads and processing until the exact command has been reviewed.

## Canonical Fields

The initial canonical loan-level fields should include:

- `activity_year`
- `source_era`
- `lei_or_respondent_id`
- `state_code`
- `county_code`
- `loan_type`
- `loan_purpose`
- `action_taken`
- `loan_amount`
- `occupancy_type`
- `lien_status`

Fintech and nonbank lender identifiers require a separate lender classification table or rule set.

## County-Year Aggregates

Initial aggregate candidates:

- total HMDA records
- non-purchase application/action records
- purchased loans
- originated loans
- denied applications
- total loan amount
- average loan amount
- lender count
- fintech lender count
- fintech application-record count
- fintech origination count
- fintech share of application records
- fintech share of originations

Fintech-specific measures depend on resolving the lender classification question.

## Approval Gates

Require explicit user approval before:

- any network request
- any data download
- any large file conversion
- any full database build
- any destructive command

The exact command must be shown before requesting approval.
