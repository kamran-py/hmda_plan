# AGENTS.md

Rules for agents working in this repository.

## Repository Boundary

- Work only inside the repository root.
- Do not inspect parent directories.
- Do not read, write, or delete files outside this repository.
- Treat generated HMDA data as large local artifacts that should not be committed.

## Safety Rules

- Do not download data unless the user first approves the exact command.
- Do not make network requests unless the user first approves the exact command.
- Do not run full-scale processing until explicitly approved.
- Do not run destructive commands unless the user first approves the exact command.
- Before any large download, large conversion, database rebuild, or destructive action, show the exact command and wait.

## Project Rules

- Use DuckDB and Parquet for large HMDA data processing.
- Do not use pandas for full raw HMDA files.
- Keep raw downloads in `data/raw`.
- Keep converted Parquet files in `data/parquet`.
- Keep DuckDB databases in `data/duckdb`.
- Keep generated summaries and committed review outputs in `output`.
- Keep implementation notes and project documentation in `docs`.
- Keep historical scaffold material in `archive/initial_scaffold`.
- Preserve the distinction between committed small outputs and generated local artifacts in public documentation.

## Data Sources

- Historic HMDA, 2007-2017:
  `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_{YEAR}_nationwide_all-records_codes.zip`
- HMDA Data Browser API, 2018-2024:
  `https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years={YEAR}`
