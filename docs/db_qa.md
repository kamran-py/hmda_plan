# DuckDB QA

## Scope

This QA pass inspects `data/duckdb/hmda_panel.duckdb`. It does not create research aggregates, classify fintech lenders, delete raw files, or delete Parquet files.

## Database Objects

| table_name | table_type |
| --- | --- |
| build_log | BASE TABLE |
| column_metadata | BASE TABLE |
| loan_years | VIEW |
| year_summary | BASE TABLE |

## Row Count Reconciliation

- `loan_years` total rows: `312,095,276`
- `conversion_metadata.json` total rows: `312,095,276`
- Match: `True`
- Years in `loan_years`: `2007-2024`
- All expected years `2007-2024` present: `True`
- `lei_or_respondent_id` column present in `loan_years`: `False`
- `lender_id` column present in `loan_years`: `True`

Note: the first DuckDB build renamed canonical `lei_or_respondent_id` to `lender_id`; missing lender identifier checks below use `lender_id`.

## Year Summary

| activity_year | row_count | state_count | county_count | lender_count | total_loan_amount |
| --- | --- | --- | --- | --- | --- |
| 2007 | 26,605,695 | 53 | 3271 | 8339 | 5,279,183,286,000 |
| 2008 | 17,391,570 | 53 | 3272 | 8127 | 3,446,236,491,000 |
| 2009 | 19,493,491 | 53 | 3271 | 7878 | 3,902,210,068,000 |
| 2010 | 16,348,557 | 53 | 3271 | 7686 | 3,370,159,156,000 |
| 2011 | 14,873,415 | 53 | 3272 | 7480 | 3,048,054,347,000 |
| 2012 | 18,691,551 | 53 | 3273 | 7253 | 3,937,513,057,000 |
| 2013 | 17,016,159 | 53 | 3273 | 7054 | 3,855,117,207,000 |
| 2014 | 12,049,341 | 52 | 3218 | 6927 | 2,599,361,472,000 |
| 2015 | 14,374,184 | 53 | 3270 | 6790 | 3,356,502,983,000 |
| 2016 | 16,332,987 | 53 | 3272 | 6644 | 4,004,530,354,000 |
| 2017 | 14,285,496 | 54 | 3274 | 5762 | 3,542,747,608,000 |
| 2018 | 15,140,471 | 57 | 7794 | 5730 | 3,624,084,705,000 |
| 2019 | 17,573,984 | 55 | 5001 | 5569 | 4,705,935,840,000 |
| 2020 | 25,699,043 | 57 | 4152 | 4527 | 8,101,087,865,000 |
| 2021 | 26,269,980 | 56 | 3974 | 4377 | 7,990,237,660,000 |
| 2022 | 16,125,975 | 56 | 3901 | 4484 | 5,385,200,245,000 |
| 2023 | 11,564,178 | 56 | 4122 | 5129 | 3,767,863,710,000 |
| 2024 | 12,259,199 | 55 | 4606 | 4926 | 3,865,432,525,000 |

## Missing Key Fields By Year

| activity_year | row_count | missing_activity_year | missing_state_code | missing_county_code | missing_lender_id | missing_loan_amount |
| --- | --- | --- | --- | --- | --- | --- |
| 2007 | 26,605,695 | 0 | 0 | 0 | 0 | 0 |
| 2008 | 17,391,570 | 0 | 0 | 0 | 0 | 0 |
| 2009 | 19,493,491 | 0 | 0 | 0 | 0 | 0 |
| 2010 | 16,348,557 | 0 | 0 | 0 | 0 | 0 |
| 2011 | 14,873,415 | 0 | 0 | 0 | 0 | 0 |
| 2012 | 18,691,551 | 0 | 0 | 0 | 0 | 0 |
| 2013 | 17,016,159 | 0 | 0 | 0 | 0 | 0 |
| 2014 | 12,049,341 | 0 | 264,330 | 320,233 | 0 | 0 |
| 2015 | 14,374,184 | 0 | 0 | 0 | 0 | 0 |
| 2016 | 16,332,987 | 0 | 0 | 0 | 0 | 0 |
| 2017 | 14,285,496 | 0 | 0 | 0 | 0 | 5,036 |
| 2018 | 15,140,471 | 0 | 1,961 | 1,961 | 1,961 | 0 |
| 2019 | 17,573,984 | 0 | 21 | 77 | 21 | 0 |
| 2020 | 25,699,043 | 0 | 0 | 0 | 0 | 0 |
| 2021 | 26,269,980 | 0 | 0 | 0 | 0 | 0 |
| 2022 | 16,125,975 | 0 | 0 | 0 | 0 | 0 |
| 2023 | 11,564,178 | 0 | 0 | 0 | 0 | 0 |
| 2024 | 12,259,199 | 0 | 0 | 0 | 0 | 0 |

## Invalid Activity Years

No invalid or unexpected `activity_year` values found.

## County Code Pattern Check

| activity_year | source_era | row_count | missing_county_code | county_3_digit | county_5_digit | county_other_format | min_county_len | max_county_len |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | pre_2018 | 26,605,695 | 0 | 25,810,685 | 0 | 795,010 | 2 | 3 |
| 2008 | pre_2018 | 17,391,570 | 0 | 16,749,950 | 0 | 641,620 | 2 | 3 |
| 2009 | pre_2018 | 19,493,491 | 0 | 18,904,271 | 0 | 589,220 | 2 | 3 |
| 2010 | pre_2018 | 16,348,557 | 0 | 15,977,069 | 0 | 371,488 | 2 | 3 |
| 2011 | pre_2018 | 14,873,415 | 0 | 14,546,297 | 0 | 327,118 | 2 | 3 |
| 2012 | pre_2018 | 18,691,551 | 0 | 18,338,628 | 0 | 352,923 | 2 | 3 |
| 2013 | pre_2018 | 17,016,159 | 0 | 16,667,382 | 0 | 348,777 | 2 | 3 |
| 2014 | pre_2018 | 12,049,341 | 320,233 | 3,428,306 | 0 | 8,300,802 | 1 | 3 |
| 2015 | pre_2018 | 14,374,184 | 0 | 14,075,664 | 0 | 298,520 | 2 | 3 |
| 2016 | pre_2018 | 16,332,987 | 0 | 16,055,239 | 0 | 277,748 | 2 | 3 |
| 2017 | pre_2018 | 14,285,496 | 0 | 14,039,899 | 0 | 245,597 | 2 | 3 |
| 2018 | post_2018 | 15,140,471 | 1,961 | 0 | 14,781,034 | 357,476 | 2 | 5 |
| 2019 | post_2018 | 17,573,984 | 77 | 0 | 17,228,582 | 345,325 | 2 | 5 |
| 2020 | post_2018 | 25,699,043 | 0 | 0 | 25,397,139 | 301,904 | 2 | 5 |
| 2021 | post_2018 | 26,269,980 | 0 | 0 | 25,971,175 | 298,805 | 2 | 5 |
| 2022 | post_2018 | 16,125,975 | 0 | 0 | 15,680,679 | 445,296 | 2 | 5 |
| 2023 | post_2018 | 11,564,178 | 0 | 0 | 11,226,505 | 337,673 | 2 | 5 |
| 2024 | post_2018 | 12,259,199 | 0 | 0 | 11,963,009 | 296,190 | 2 | 5 |

Interpretation: pre-2018 county codes are mostly 3-digit county components, while post-2018 county codes are mostly 5-digit full county FIPS codes. They are not directly consistent across eras and should be normalized before county-level aggregation.

## County Code Other-Format Samples

| source_era | county_code | row_count |
| --- | --- | --- |
| pre_2018 | NA  | 4002424 |
| post_2018 | NA | 2382650 |
| pre_2018 | 37 | 409448 |
| pre_2018 | 13 | 398349 |
| pre_2018 | 31 | 372637 |
| pre_2018 | 3 | 355946 |
| pre_2018 | 1 | 297538 |
| pre_2018 | 59 | 279829 |
| pre_2018 | NA | 245597 |
| pre_2018 | 5 | 240738 |
| pre_2018 | 29 | 220053 |
| pre_2018 | 73 | 216359 |
| pre_2018 | 17 | 204975 |
| pre_2018 | 33 | 198403 |
| pre_2018 | 67 | 198377 |
| pre_2018 | 35 | 195835 |
| pre_2018 | 71 | 191102 |
| pre_2018 | 19 | 190081 |
| pre_2018 | 85 | 184664 |
| pre_2018 | 11 | 182748 |

## State Code Pattern Check

| activity_year | source_era | row_count | distinct_state_values | missing_state_code | state_2_digit | state_2_alpha | state_other_format |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | pre_2018 | 26,605,695 | 53 | 0 | 25,916,848 | 688,847 | 0 |
| 2008 | pre_2018 | 17,391,570 | 53 | 0 | 16,808,055 | 583,515 | 0 |
| 2009 | pre_2018 | 19,493,491 | 53 | 0 | 18,971,044 | 522,447 | 0 |
| 2010 | pre_2018 | 16,348,557 | 53 | 0 | 16,025,630 | 322,927 | 0 |
| 2011 | pre_2018 | 14,873,415 | 53 | 0 | 14,588,486 | 284,929 | 0 |
| 2012 | pre_2018 | 18,691,551 | 53 | 0 | 18,375,848 | 315,703 | 0 |
| 2013 | pre_2018 | 17,016,159 | 53 | 0 | 16,702,522 | 313,637 | 0 |
| 2014 | pre_2018 | 12,049,341 | 52 | 264,330 | 9,284,983 | 0 | 2,500,028 |
| 2015 | pre_2018 | 14,374,184 | 53 | 0 | 14,108,175 | 266,009 | 0 |
| 2016 | pre_2018 | 16,332,987 | 53 | 0 | 16,078,416 | 254,571 | 0 |
| 2017 | pre_2018 | 14,285,496 | 54 | 0 | 14,088,338 | 197,158 | 0 |
| 2018 | post_2018 | 15,140,471 | 57 | 1,961 | 0 | 15,138,510 | 0 |
| 2019 | post_2018 | 17,573,984 | 55 | 21 | 0 | 17,573,963 | 0 |
| 2020 | post_2018 | 25,699,043 | 57 | 0 | 0 | 25,699,043 | 0 |
| 2021 | post_2018 | 26,269,980 | 56 | 0 | 0 | 26,269,980 | 0 |
| 2022 | post_2018 | 16,125,975 | 56 | 0 | 0 | 16,125,975 | 0 |
| 2023 | post_2018 | 11,564,178 | 56 | 0 | 0 | 11,564,178 | 0 |
| 2024 | post_2018 | 12,259,199 | 55 | 0 | 0 | 12,259,199 | 0 |

Interpretation: pre-2018 state codes are numeric/FIPS-style two-character codes, while post-2018 state codes are mostly two-letter abbreviations. They are not directly consistent across eras and should be normalized before geographic panel construction.

## State Code Other-Format Samples

| source_era | state_code | row_count |
| --- | --- | --- |
| pre_2018 | 6 | 1436457 |
| pre_2018 | 4 | 317345 |
| pre_2018 | 8 | 313445 |
| pre_2018 | 1 | 182825 |
| pre_2018 | 9 | 114931 |
| pre_2018 | 5 | 108526 |
| pre_2018 | 2 | 26499 |

## QA Conclusions

- `loan_years` row count matches `conversion_metadata.json`.
- All years `2007-2024` are present.
- No invalid `activity_year` values were found.
- `state_code` and `county_code` have era-specific formats and require normalization before county-year research aggregates.
- `lender_id` is available for all years, but historic respondent IDs and post-2018 LEIs are different identifier systems.
- Missing `loan_amount` exists in small numbers in some post-2018 years; aggregation code should decide whether to exclude or separately count missing amounts.
