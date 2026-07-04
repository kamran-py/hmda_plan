from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a smoke-test configuration is invalid."""


@dataclass(frozen=True)
class SmokeTestConfig:
    years: tuple[int, int]
    input_mode: str
    max_rows_per_year: int
    required_columns: tuple[str, ...]
    checks: tuple[str, ...]


def load_smoke_test_config(path: str | Path) -> SmokeTestConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return parse_smoke_test_config(raw)


def parse_smoke_test_config(raw: dict[str, Any]) -> SmokeTestConfig:
    years = raw.get("years")
    if not isinstance(years, list) or len(years) != 2:
        raise ConfigError("years must contain exactly two entries")
    if not all(isinstance(year, int) for year in years):
        raise ConfigError("years must be integers")
    if len(set(years)) != 2:
        raise ConfigError("years must be distinct")

    input_mode = raw.get("input_mode")
    if input_mode != "manifest_only":
        raise ConfigError("input_mode must be manifest_only for the initial scaffold")

    max_rows_per_year = raw.get("max_rows_per_year")
    if not isinstance(max_rows_per_year, int) or max_rows_per_year <= 0:
        raise ConfigError("max_rows_per_year must be a positive integer")

    required_columns = raw.get("required_columns")
    if not isinstance(required_columns, list) or not required_columns:
        raise ConfigError("required_columns must be a non-empty list")
    if not all(isinstance(column, str) and column for column in required_columns):
        raise ConfigError("required_columns must contain non-empty strings")

    checks = raw.get("checks", [])
    if not isinstance(checks, list):
        raise ConfigError("checks must be a list")
    if not all(isinstance(check, str) and check for check in checks):
        raise ConfigError("checks must contain non-empty strings")

    return SmokeTestConfig(
        years=(years[0], years[1]),
        input_mode=input_mode,
        max_rows_per_year=max_rows_per_year,
        required_columns=tuple(required_columns),
        checks=tuple(checks),
    )
