# Two-Year Smoke-Test Design

## Objective

Create a small, repeatable HMDA workflow test that proves the project wiring is correct before any full-scale data download or processing starts.

The smoke test is intentionally limited to two years and a capped row count per year. It should exercise configuration, file discovery, schema expectations, minimal parsing, and summary checks without becoming a production run.

## Current Constraints

- No network requests without prior approval of the exact command.
- No large downloads without prior approval of the exact command.
- No full-scale processing yet.
- No destructive commands.
- Work remains inside this repository.

## Year Selection

The smoke-test configuration requires exactly two distinct years. The example config uses `2022` and `2023` as placeholders.

Before using real HMDA files, confirm the available local data inventory and update the config years if needed. If data must be downloaded, pause and approve the exact download command first.

## Proposed Smoke-Test Flow

1. Load and validate the smoke-test config.
2. Confirm exactly two distinct years are present.
3. Confirm required column names are declared.
4. Confirm a per-year row cap is declared.
5. In a later approved phase, discover local input files for each year.
6. In a later approved phase, read only up to the configured row cap per year.
7. In a later approved phase, verify required columns exist.
8. In a later approved phase, produce compact per-year summary counts.

## Initial Checks

- `config_valid`: Config can be parsed as JSON.
- `year_pair_present`: Exactly two distinct integer years are configured.
- `required_columns_declared`: Required column list is non-empty.
- `row_limit_declared`: Row cap is a positive integer.
- `no_network_required`: Current smoke-test mode does not require network access.

## Later Approval Gates

These steps should not run until explicitly approved:

- Downloading HMDA files.
- Expanding compressed datasets.
- Reading large local files beyond the configured row cap.
- Writing derived datasets.
- Running production-scale transformations.

## Success Criteria

The initial scaffold succeeds when the dry run prints a deterministic plan for two configured years and the unit tests pass locally.
