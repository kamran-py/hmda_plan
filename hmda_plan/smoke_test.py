from __future__ import annotations

import argparse
from collections.abc import Sequence

from hmda_plan.config import SmokeTestConfig, load_smoke_test_config


def build_plan(config: SmokeTestConfig) -> list[str]:
    year_list = ", ".join(str(year) for year in config.years)
    column_list = ", ".join(config.required_columns)
    check_list = ", ".join(config.checks) if config.checks else "none"

    return [
        "HMDA two-year smoke-test dry run",
        f"Years: {year_list}",
        f"Input mode: {config.input_mode}",
        f"Maximum rows per year: {config.max_rows_per_year}",
        f"Required columns: {column_list}",
        f"Declared checks: {check_list}",
        "No network requests will be made.",
        "No full-scale processing will be run.",
    ]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the HMDA smoke-test dry-run plan.")
    parser.add_argument("--config", required=True, help="Path to a smoke-test JSON config.")
    args = parser.parse_args(argv)

    config = load_smoke_test_config(args.config)
    for line in build_plan(config):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
