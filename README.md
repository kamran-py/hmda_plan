# HMDA Plan

Lightweight project scaffold for planning HMDA data workflows without running full-scale processing.

This repository currently contains only local planning code and documentation. It does not download HMDA data, call external services, or perform large conversions.

## Current Scope

- Define a reproducible two-year smoke-test design.
- Validate a smoke-test configuration.
- Print a dry-run execution plan.
- Keep full-scale ingestion, transformation, and analysis out of scope until explicitly approved.

## Repository Layout

```text
configs/
  smoke_test.example.json   Example two-year smoke-test configuration.
docs/
  smoke-test-design.md      Smoke-test goals, constraints, checks, and approval gates.
hmda_plan/
  config.py                 Config loading and validation.
  smoke_test.py             Dry-run smoke-test planner.
tests/
  test_smoke_plan.py        Unit tests for config validation and plan output.
```

## Local Smoke-Test Dry Run

```powershell
python -m hmda_plan.smoke_test --config configs\smoke_test.example.json
```

This command only validates config and prints the planned steps. It does not read HMDA data files unless paths are added later and does not make network requests.

## Guardrails

- Network requests require explicit approval of the exact command.
- Large downloads, large conversions, destructive commands, and full-scale processing require explicit approval first.
- Smoke-test years are configurable. The included example uses `2022` and `2023` as placeholders until a data inventory is approved.
