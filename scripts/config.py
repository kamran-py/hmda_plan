from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PARQUET_DIR = DATA_DIR / "parquet"
DUCKDB_DIR = DATA_DIR / "duckdb"
OUTPUT_DIR = PROJECT_ROOT / "output"

ALL_YEARS = tuple(range(2007, 2025))
SMOKE_TEST_YEARS = (2007, 2018)
PRE_2018_YEARS = tuple(range(2007, 2018))
POST_2018_YEARS = tuple(range(2018, 2025))

HISTORIC_URL_TEMPLATE = (
    "https://files.consumerfinance.gov/hmda-historic-loan-data/"
    "hmda_{year}_nationwide_all-records_codes.zip"
)
DATA_BROWSER_URL_TEMPLATE = (
    "https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years={year}"
)

DEFAULT_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-before-download)"
USER_AGENT_ENV_VAR = "HMDA_USER_AGENT"


def get_user_agent() -> str:
    return os.environ.get(USER_AGENT_ENV_VAR, DEFAULT_USER_AGENT)


@dataclass(frozen=True)
class YearSpec:
    year: int
    source_era: str
    url: str
    raw_path: Path
    parquet_path: Path


CANONICAL_COLUMNS = {
    "activity_year": "INTEGER",
    "source_era": "VARCHAR",
    "lei_or_respondent_id": "VARCHAR",
    "state_code": "VARCHAR",
    "county_code": "VARCHAR",
    "loan_type": "VARCHAR",
    "loan_purpose": "VARCHAR",
    "action_taken": "VARCHAR",
    "loan_amount": "DOUBLE",
    "occupancy_type": "VARCHAR",
    "lien_status": "VARCHAR",
}

PRE_2018_COLUMN_MAP = {
    "as_of_year": "activity_year",
    "respondent_id": "lei_or_respondent_id",
    "state_code": "state_code",
    "county_code": "county_code",
    "loan_type": "loan_type",
    "loan_purpose": "loan_purpose",
    "action_taken": "action_taken",
    "loan_amount_000s": "loan_amount",
    "owner_occupancy": "occupancy_type",
    "lien_status": "lien_status",
}

POST_2018_COLUMN_MAP = {
    "activity_year": "activity_year",
    "lei": "lei_or_respondent_id",
    "state_code": "state_code",
    "county_code": "county_code",
    "loan_type": "loan_type",
    "loan_purpose": "loan_purpose",
    "action_taken": "action_taken",
    "loan_amount": "loan_amount",
    "occupancy_type": "occupancy_type",
    "lien_status": "lien_status",
}

COLUMN_DESCRIPTIONS = {
    "activity_year": "HMDA reporting year.",
    "source_era": "Schema era: pre_2018 historic files or post_2018 Data Browser files.",
    "lei_or_respondent_id": "Legal Entity Identifier for post-2018 records or respondent_id for historic records.",
    "state_code": "State FIPS code when available.",
    "county_code": "County FIPS code when available.",
    "loan_type": "HMDA loan type code.",
    "loan_purpose": "HMDA loan purpose code.",
    "action_taken": "HMDA action taken code.",
    "loan_amount": "Loan amount. Historic files may require unit normalization.",
    "occupancy_type": "Owner occupancy or occupancy type code.",
    "lien_status": "Lien status code.",
}


def validate_year(year: int) -> None:
    if year not in ALL_YEARS:
        raise ValueError(f"Unsupported HMDA year: {year}")


def source_era_for_year(year: int) -> str:
    validate_year(year)
    return "pre_2018" if year <= 2017 else "post_2018"


def url_for_year(year: int) -> str:
    era = source_era_for_year(year)
    if era == "pre_2018":
        return HISTORIC_URL_TEMPLATE.format(year=year)
    return DATA_BROWSER_URL_TEMPLATE.format(year=year)


def raw_filename_for_year(year: int) -> str:
    era = source_era_for_year(year)
    suffix = "zip" if era == "pre_2018" else "csv"
    return f"hmda_{year}_nationwide.{suffix}"


def year_spec(year: int) -> YearSpec:
    era = source_era_for_year(year)
    return YearSpec(
        year=year,
        source_era=era,
        url=url_for_year(year),
        raw_path=RAW_DIR / raw_filename_for_year(year),
        parquet_path=PARQUET_DIR / f"hmda_{year}.parquet",
    )


def column_map_for_year(year: int) -> dict[str, str]:
    era = source_era_for_year(year)
    return PRE_2018_COLUMN_MAP if era == "pre_2018" else POST_2018_COLUMN_MAP
