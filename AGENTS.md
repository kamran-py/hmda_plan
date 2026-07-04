# AGENTS.md

Rules for agents working in this repository.

## Repository Boundary

- Work only inside this repository: `C:\Users\kanop\hmda_plan`.
- Do not inspect parent directories.
- Do not read, write, or delete files outside this repository.
- Treat generated HMDA data as large local artifacts that should not be committed.

## Safety Rules

- Do not download any data unless the user first approves the exact command.
- Do not make network requests unless the user first approves the exact command.
- Do not run full-scale processing until explicitly approved.
- Do not run destructive commands unless the user first approves the exact command.
- Before any large download, large conversion, database rebuild, or destructive action, show the exact command and wait.

## Project Rules

- Use DuckDB and Parquet for large HMDA data processing.
- Do not use pandas for full raw HMDA files.
- Design smoke tests around two years only: `2007` for the historic format and `2018` for the post-2018 format.
- Keep raw downloads in `data/raw`.
- Keep converted Parquet files in `data/parquet`.
- Keep DuckDB databases in `data/duckdb`.
- Keep generated summaries and exports in `output`.
- Keep implementation notes and progress logs in `docs`.

## Data Sources

- Historic HMDA, 2007-2017:
  `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_{YEAR}_nationwide_all-records_codes.zip`
- HMDA Data Browser API, 2018-2024:
  `https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years={YEAR}`

## Phase 1 Scope

Phase 1 is scaffolding only. It may create folders, documentation, and starter code. It must not download data, convert full files, or build the full database.
