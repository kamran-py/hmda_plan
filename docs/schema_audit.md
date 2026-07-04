# HMDA Parquet Schema Audit

## Scope

This audit inspects the 18 annual Parquet files in `data/parquet` using DuckDB metadata queries. It does not build a DuckDB database, aggregate data, delete raw files, or modify raw inputs.

## Metadata Summary

- Metadata file: `data\parquet\conversion_metadata.json`
- Metadata records: `18`
- Years covered: `2007-2024`
- Total rows: `312095276`
- Conversion statuses present: `converted, skipped_existing`
- Metadata errors: `0`

## Column Counts

| Year | Columns |
| --- | --- |
| 2007 | 48 |
| 2008 | 48 |
| 2009 | 48 |
| 2010 | 48 |
| 2011 | 48 |
| 2012 | 48 |
| 2013 | 48 |
| 2014 | 48 |
| 2015 | 48 |
| 2016 | 48 |
| 2017 | 48 |
| 2018 | 102 |
| 2019 | 102 |
| 2020 | 102 |
| 2021 | 102 |
| 2022 | 102 |
| 2023 | 102 |
| 2024 | 102 |

## Columns Common To All Years

`action_taken`, `activity_year`, `applicant_sex`, `county_code`, `hoepa_status`, `lei_or_respondent_id`, `lien_status`, `loan_purpose`, `loan_type`, `preapproval`, `purchaser_type`, `rate_spread`, `source_era`, `state_code`

## Columns Only In Pre-2018 Years

`agency_code`, `applicant_ethnicity`, `applicant_income_000s`, `applicant_race_1`, `applicant_race_2`, `applicant_race_3`, `applicant_race_4`, `applicant_race_5`, `application_date_indicator`, `as_of_year`, `census_tract_number`, `co_applicant_ethnicity`, `co_applicant_race_1`, `co_applicant_race_2`, `co_applicant_race_3`, `co_applicant_race_4`, `co_applicant_race_5`, `co_applicant_sex`, `denial_reason_1`, `denial_reason_2`, `denial_reason_3`, `edit_status`, `hud_median_family_income`, `loan_amount_000s`, `minority_population`, `msamd`, `number_of_1_to_4_family_units`, `number_of_owner_occupied_units`, `owner_occupancy`, `population`, `property_type`, `respondent_id`, `sequence_number`, `tract_to_msamd_income`

## Columns Only In Post-2018 Years

`applicant_age`, `applicant_age_above_62`, `applicant_credit_score_type`, `applicant_ethnicity-1`, `applicant_ethnicity-2`, `applicant_ethnicity-3`, `applicant_ethnicity-4`, `applicant_ethnicity-5`, `applicant_ethnicity_observed`, `applicant_race-1`, `applicant_race-2`, `applicant_race-3`, `applicant_race-4`, `applicant_race-5`, `applicant_race_observed`, `applicant_sex_observed`, `aus-1`, `aus-2`, `aus-3`, `aus-4`, `aus-5`, `balloon_payment`, `business_or_commercial_purpose`, `census_tract`, `co-applicant_age`, `co-applicant_age_above_62`, `co-applicant_credit_score_type`, `co-applicant_ethnicity-1`, `co-applicant_ethnicity-2`, `co-applicant_ethnicity-3`, `co-applicant_ethnicity-4`, `co-applicant_ethnicity-5`, `co-applicant_ethnicity_observed`, `co-applicant_race-1`, `co-applicant_race-2`, `co-applicant_race-3`, `co-applicant_race-4`, `co-applicant_race-5`, `co-applicant_race_observed`, `co-applicant_sex`, `co-applicant_sex_observed`, `conforming_loan_limit`, `construction_method`, `debt_to_income_ratio`, `denial_reason-1`, `denial_reason-2`, `denial_reason-3`, `denial_reason-4`, `derived_dwelling_category`, `derived_ethnicity`, `derived_loan_product_type`, `derived_msa-md`, `derived_race`, `derived_sex`, `discount_points`, `ffiec_msa_md_median_family_income`, `income`, `initially_payable_to_institution`, `interest_only_payment`, `interest_rate`, `intro_rate_period`, `lei`, `lender_credits`, `loan_amount`, `loan_term`, `loan_to_value_ratio`, `manufactured_home_land_property_interest`, `manufactured_home_secured_property_type`, `multifamily_affordable_units`, `negative_amortization`, `occupancy_type`, `open-end_line_of_credit`, `origination_charges`, `other_nonamortizing_features`, `prepayment_penalty_term`, `property_value`, `raw_activity_year`, `reverse_mortgage`, `submission_of_application`, `total_loan_costs`, `total_points_and_fees`, `total_units`, `tract_median_age_of_housing_units`, `tract_minority_population_percent`, `tract_one_to_four_family_homes`, `tract_owner_occupied_units`, `tract_population`, `tract_to_msa_income_percentage`

## Column Type Differences Across Years

No column type differences were found for columns sharing the same name across years.

## Key Field Availability

| Logical field | Observed columns | Years present |
| --- | --- | --- |
| activity_year | activity_year, as_of_year, raw_activity_year | 2007-2024 |
| state_code | state_code | 2007-2024 |
| county_code | county_code | 2007-2024 |
| census_tract | census_tract, census_tract_number | 2007-2024 |
| lei_or_respondent_id | lei, lei_or_respondent_id, respondent_id | 2007-2024 |
| lender_name_fields | none found | none |
| loan_amount | loan_amount, loan_amount_000s | 2007-2024 |
| loan_type | loan_type | 2007-2024 |
| loan_purpose | loan_purpose | 2007-2024 |
| occupancy_type | occupancy_type, owner_occupancy | 2007-2024 |
| action_taken | action_taken | 2007-2024 |
| applicant_income | applicant_income_000s, income | 2007-2024 |
| race_fields | applicant_race-1, applicant_race-2, applicant_race-3, applicant_race-4, applicant_race-5, applicant_race_1, applicant_race_2, applicant_race_3, applicant_race_4, applicant_race_5, co-applicant_race-1, co-applicant_race-2, co-applicant_race-3, co-applicant_race-4, co-applicant_race-5, co_applicant_race_1, co_applicant_race_2, co_applicant_race_3, co_applicant_race_4, co_applicant_race_5, derived_race | 2007-2024 |

## Recommended Canonical Schema For First DuckDB Build

| Column | Type | Source | Note |
| --- | --- | --- | --- |
| activity_year | INTEGER | activity_year | Already canonical in all converted Parquet files. |
| source_era | VARCHAR | source_era | pre_2018 for 2007-2017 and post_2018 for 2018-2024. |
| lender_id | VARCHAR | lei_or_respondent_id | Historic respondent_id and post-2018 LEI are not equivalent ID systems. |
| lender_id_type | VARCHAR | derived from source_era | Use respondent_id for pre_2018 and lei for post_2018. |
| state_code | VARCHAR | state_code | Preserve leading zeros. |
| county_code | VARCHAR | county_code | Preserve leading zeros and missing/suppressed codes. |
| census_tract | VARCHAR | census_tract_number for pre_2018; census_tract for post_2018 | Keep as text because formats differ across eras. |
| loan_amount | DOUBLE | loan_amount_000s for pre_2018; loan_amount for post_2018 | For comparable dollars, multiply historic loan_amount_000s by 1000. |
| loan_type | VARCHAR | loan_type | Code meanings should be documented in metadata tables. |
| loan_purpose | VARCHAR | loan_purpose | Code meanings changed across HMDA eras and need metadata. |
| occupancy_type | VARCHAR | owner_occupancy for pre_2018; occupancy_type for post_2018 | Era-specific code values need metadata. |
| action_taken | VARCHAR | action_taken | Use coded values for aggregation definitions. |
| applicant_income | DOUBLE | applicant_income_000s for pre_2018; income for post_2018 | Confirm units before analysis; historic field is explicitly in thousands. |
| raw_source_columns | STRUCT or retained wide columns | era-specific raw columns | Retain raw fields during initial DuckDB build for debugging schema differences. |

## Notes

- `activity_year`, `source_era`, `lei_or_respondent_id`, `state_code`, `county_code`, `loan_type`, `loan_purpose`, and `action_taken` are already common across all years.
- Historic `loan_amount_000s` and post-2018 `loan_amount` should be normalized into a canonical dollar-denominated `loan_amount` field before cross-era analysis.
- Historic `owner_occupancy` and post-2018 `occupancy_type` should be mapped into canonical `occupancy_type`.
- Historic `applicant_income_000s` and post-2018 `income` should be mapped carefully after confirming units.
- No lender-name field is present in these Parquet schemas; lender classification will need an external lender crosswalk or metadata source.
- Race fields are era-specific and should remain available as raw columns while canonical race/ethnicity handling is designed.
