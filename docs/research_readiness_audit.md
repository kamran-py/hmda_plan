# Research Readiness Audit

## Scope

This audit checks whether `county_year_lending` and `loan_years_geo` are ready to support lender-level and fintech-expansion analysis. It does not create new research aggregates, classify fintech lenders, or export final CSVs.

## County-Year Aggregate Summary

- Row count: `58,006`
- Years covered: `2007-2024`
- Year count: `18`
- Total records: `305,141,850`
- Application records: `259,119,806`
- Purchased loans: `46,022,044`
- Total applications legacy field: `305,141,850`
- Originated loans: `155,554,418`
- Denied applications: `48,614,948`
- Total loan amount: `75,734,874,727,000`

## County-Year Checks

| null_activity_year | null_state_fips_2 | null_county_fips_5 |
| --- | --- | --- |
| 0 | 0 | 0 |

| duplicate_grain_rows |
| --- |
| 0 |

## County-Year Metrics By Year

| activity_year | county_count | total_records | application_records | purchased_loans | total_applications | originated_loans | denied_applications | total_loan_amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 3,218 | 25,810,685 | 21,072,710 | 4,737,975 | 25,810,685 | 10,363,770 | 5,819,928 | 5,146,875,752,000 |
| 2008 | 3,219 | 16,749,950 | 13,849,145 | 2,900,805 | 16,749,950 | 7,092,935 | 3,789,609 | 3,350,860,801,000 |
| 2009 | 3,218 | 18,904,271 | 14,626,912 | 4,277,359 | 18,904,271 | 8,839,646 | 2,870,671 | 3,812,953,809,000 |
| 2010 | 3,218 | 15,977,069 | 12,756,506 | 3,220,563 | 15,977,069 | 7,810,204 | 2,482,053 | 3,313,976,640,000 |
| 2011 | 3,219 | 14,546,297 | 11,610,525 | 2,935,772 | 14,546,297 | 7,056,938 | 2,308,251 | 2,992,138,358,000 |
| 2012 | 3,220 | 18,338,628 | 15,174,893 | 3,163,735 | 18,338,628 | 9,739,921 | 2,718,055 | 3,872,898,552,000 |
| 2013 | 3,220 | 16,667,382 | 13,875,206 | 2,792,176 | 16,667,382 | 8,678,842 | 2,607,088 | 3,786,987,064,000 |
| 2014 | 3,218 | 11,729,108 | 9,934,128 | 1,794,980 | 11,729,108 | 6,019,168 | 2,018,466 | 2,536,226,723,000 |
| 2015 | 3,217 | 14,075,664 | 11,975,714 | 2,099,950 | 14,075,664 | 7,383,304 | 2,232,849 | 3,297,102,667,000 |
| 2016 | 3,219 | 16,055,239 | 13,826,628 | 2,228,611 | 16,055,239 | 8,358,154 | 2,645,324 | 3,939,731,541,000 |
| 2017 | 3,220 | 14,039,899 | 11,955,535 | 2,084,364 | 14,039,899 | 7,324,077 | 1,971,050 | 3,488,812,000,000 |
| 2018 | 3,261 | 14,780,569 | 12,770,422 | 2,010,147 | 14,780,569 | 7,697,135 | 2,479,327 | 3,535,319,885,000 |
| 2019 | 3,223 | 17,228,582 | 14,958,693 | 2,269,889 | 17,228,582 | 9,308,852 | 2,462,341 | 4,618,373,140,000 |
| 2020 | 3,222 | 25,397,139 | 22,621,049 | 2,776,090 | 25,397,139 | 14,608,161 | 2,813,404 | 7,776,721,675,000 |
| 2021 | 3,223 | 25,971,175 | 23,273,062 | 2,698,113 | 25,971,175 | 15,047,525 | 2,900,186 | 7,885,035,955,000 |
| 2022 | 3,224 | 15,680,679 | 14,180,296 | 1,500,383 | 15,680,679 | 8,368,999 | 2,451,649 | 5,224,483,635,000 |
| 2023 | 3,224 | 11,226,505 | 9,971,284 | 1,255,221 | 11,226,505 | 5,686,639 | 1,991,157 | 3,404,933,745,000 |
| 2024 | 3,223 | 11,963,009 | 10,687,098 | 1,275,911 | 11,963,009 | 6,170,148 | 2,053,540 | 3,751,442,785,000 |

## Reconciliation Against Loan-Level Geography

The aggregate record count should equal `loan_years_geo` rows where `county_fips_5` is present. Excluded rows should equal `county_year_lending_missing_geo_qa`.

| loan_years_geo_rows | expected_included_records | aggregate_included_records | included_difference | expected_excluded_missing_geo | qa_excluded_missing_geo | excluded_difference |
| --- | --- | --- | --- | --- | --- | --- |
| 312,095,276 | 305,141,850 | 305,141,850 | 0 | 6,953,426 | 6,953,426 | 0 |

| activity_year | loan_years_geo_rows | expected_included_records | aggregate_included_records | included_difference | expected_excluded_missing_geo | qa_excluded_missing_geo | excluded_difference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 26,605,695 | 25,810,685 | 25,810,685 | 0 | 795,010 | 795,010 | 0 |
| 2008 | 17,391,570 | 16,749,950 | 16,749,950 | 0 | 641,620 | 641,620 | 0 |
| 2009 | 19,493,491 | 18,904,271 | 18,904,271 | 0 | 589,220 | 589,220 | 0 |
| 2010 | 16,348,557 | 15,977,069 | 15,977,069 | 0 | 371,488 | 371,488 | 0 |
| 2011 | 14,873,415 | 14,546,297 | 14,546,297 | 0 | 327,118 | 327,118 | 0 |
| 2012 | 18,691,551 | 18,338,628 | 18,338,628 | 0 | 352,923 | 352,923 | 0 |
| 2013 | 17,016,159 | 16,667,382 | 16,667,382 | 0 | 348,777 | 348,777 | 0 |
| 2014 | 12,049,341 | 11,729,108 | 11,729,108 | 0 | 320,233 | 320,233 | 0 |
| 2015 | 14,374,184 | 14,075,664 | 14,075,664 | 0 | 298,520 | 298,520 | 0 |
| 2016 | 16,332,987 | 16,055,239 | 16,055,239 | 0 | 277,748 | 277,748 | 0 |
| 2017 | 14,285,496 | 14,039,899 | 14,039,899 | 0 | 245,597 | 245,597 | 0 |
| 2018 | 15,140,471 | 14,780,569 | 14,780,569 | 0 | 359,902 | 359,902 | 0 |
| 2019 | 17,573,984 | 17,228,582 | 17,228,582 | 0 | 345,402 | 345,402 | 0 |
| 2020 | 25,699,043 | 25,397,139 | 25,397,139 | 0 | 301,904 | 301,904 | 0 |
| 2021 | 26,269,980 | 25,971,175 | 25,971,175 | 0 | 298,805 | 298,805 | 0 |
| 2022 | 16,125,975 | 15,680,679 | 15,680,679 | 0 | 445,296 | 445,296 | 0 |
| 2023 | 11,564,178 | 11,226,505 | 11,226,505 | 0 | 337,673 | 337,673 | 0 |
| 2024 | 12,259,199 | 11,963,009 | 11,963,009 | 0 | 296,190 | 296,190 | 0 |

## Lender Fields

- Canonical lender identifier column: `lender_id`.
- Identifier type column: `lender_id_type`.
- `lender_id_type` is `respondent_id` for pre-2018 data and `lei` for post-2018 data.
- Historic respondent IDs and post-2018 LEIs are not the same identifier system, so cross-era lender identity resolution remains a separate task.
- Explicit lender-name columns in `loan_years_geo`: `none`.
- Lender-name keys retained in `raw_source_columns`: `none`.
- Available lender identifier/name-like columns in `loan_years_geo`: `lender_id, lender_id_type`.
- Available lender identifier/name-like keys retained in `raw_source_columns`: `lei, respondent_id`.
- Raw source keys sampled: `applicant_income_000s, as_of_year, census_tract, census_tract_number, income, lei, loan_amount, loan_amount_000s, occupancy_type, owner_occupancy, raw_activity_year, respondent_id`.

## Lender Identifier Coverage By Year

| activity_year | row_count | missing_lender_id | distinct_lenders | lender_id_type_count |
| --- | --- | --- | --- | --- |
| 2007 | 26,605,695 | 0 | 8,339 | 1 |
| 2008 | 17,391,570 | 0 | 8,127 | 1 |
| 2009 | 19,493,491 | 0 | 7,878 | 1 |
| 2010 | 16,348,557 | 0 | 7,686 | 1 |
| 2011 | 14,873,415 | 0 | 7,480 | 1 |
| 2012 | 18,691,551 | 0 | 7,253 | 1 |
| 2013 | 17,016,159 | 0 | 7,054 | 1 |
| 2014 | 12,049,341 | 0 | 6,927 | 1 |
| 2015 | 14,374,184 | 0 | 6,790 | 1 |
| 2016 | 16,332,987 | 0 | 6,644 | 1 |
| 2017 | 14,285,496 | 0 | 5,762 | 1 |
| 2018 | 15,140,471 | 1,961 | 5,730 | 1 |
| 2019 | 17,573,984 | 21 | 5,569 | 1 |
| 2020 | 25,699,043 | 0 | 4,527 | 1 |
| 2021 | 26,269,980 | 0 | 4,377 | 1 |
| 2022 | 16,125,975 | 0 | 4,484 | 1 |
| 2023 | 11,564,178 | 0 | 5,129 | 1 |
| 2024 | 12,259,199 | 0 | 4,926 | 1 |

## Lender Identifier Types

| source_era | lender_id_type | min_year | max_year | row_count |
| --- | --- | --- | --- | --- |
| pre_2018 | respondent_id | 2007 | 2017 | 187,462,446 |
| post_2018 | lei | 2018 | 2024 | 124,632,830 |

## Action Taken Mapping

- Originated loans count `action_taken = '1'`.
- Denied applications count `action_taken = '3'`.
- Application records count non-purchase action records with `action_taken` in `1`, `2`, `3`, `4`, `5`, `7`, or `8`.
- Purchased loans count `action_taken = '6'` and are excluded from `application_records`.
- Action code `7` is documented as preapproval denied but is not included in `denied_applications`.

| source_era | action_taken | action_description | counts_as_origination | counts_as_denial |
| --- | --- | --- | --- | --- |
| post_2018 | 1 | Loan originated | True | False |
| post_2018 | 2 | Application approved but not accepted | False | False |
| post_2018 | 3 | Application denied | False | True |
| post_2018 | 4 | Application withdrawn by applicant | False | False |
| post_2018 | 5 | File closed for incompleteness | False | False |
| post_2018 | 6 | Loan purchased by institution | False | False |
| post_2018 | 7 | Preapproval request denied | False | False |
| post_2018 | 8 | Preapproval request approved but not accepted | False | False |
| pre_2018 | 1 | Loan originated | True | False |
| pre_2018 | 2 | Application approved but not accepted | False | False |
| pre_2018 | 3 | Application denied | False | True |
| pre_2018 | 4 | Application withdrawn by applicant | False | False |
| pre_2018 | 5 | File closed for incompleteness | False | False |
| pre_2018 | 6 | Loan purchased by institution | False | False |
| pre_2018 | 7 | Preapproval request denied | False | False |
| pre_2018 | 8 | Preapproval request approved but not accepted | False | False |

## Action Taken Counts By Year

| activity_year | source_era | action_taken | row_count |
| --- | --- | --- | --- |
| 2007 | pre_2018 | 1 | 10,441,545 |
| 2007 | pre_2018 | 2 | 1,945,380 |
| 2007 | pre_2018 | 3 | 5,952,530 |
| 2007 | pre_2018 | 4 | 2,331,997 |
| 2007 | pre_2018 | 5 | 719,921 |
| 2007 | pre_2018 | 6 | 4,781,414 |
| 2007 | pre_2018 | 7 | 235,434 |
| 2007 | pre_2018 | 8 | 197,474 |
| 2008 | pre_2018 | 1 | 7,177,262 |
| 2008 | pre_2018 | 2 | 1,105,492 |
| 2008 | pre_2018 | 3 | 3,944,602 |
| 2008 | pre_2018 | 4 | 1,552,895 |
| 2008 | pre_2018 | 5 | 413,690 |
| 2008 | pre_2018 | 6 | 2,921,821 |
| 2008 | pre_2018 | 7 | 176,544 |
| 2008 | pre_2018 | 8 | 99,264 |
| 2009 | pre_2018 | 1 | 8,950,936 |
| 2009 | pre_2018 | 2 | 851,769 |
| 2009 | pre_2018 | 3 | 3,012,967 |
| 2009 | pre_2018 | 4 | 1,727,739 |
| 2009 | pre_2018 | 5 | 446,497 |
| 2009 | pre_2018 | 6 | 4,294,528 |
| 2009 | pre_2018 | 7 | 148,966 |
| 2009 | pre_2018 | 8 | 60,089 |
| 2010 | pre_2018 | 1 | 7,863,337 |
| 2010 | pre_2018 | 2 | 650,594 |
| 2010 | pre_2018 | 3 | 2,556,789 |
| 2010 | pre_2018 | 4 | 1,448,330 |
| 2010 | pre_2018 | 5 | 435,825 |
| 2010 | pre_2018 | 6 | 3,229,010 |
| 2010 | pre_2018 | 7 | 112,881 |
| 2010 | pre_2018 | 8 | 51,791 |
| 2011 | pre_2018 | 1 | 7,095,262 |
| 2011 | pre_2018 | 2 | 636,467 |
| 2011 | pre_2018 | 3 | 2,354,846 |
| 2011 | pre_2018 | 4 | 1,225,751 |
| 2011 | pre_2018 | 5 | 430,484 |
| 2011 | pre_2018 | 6 | 2,944,662 |
| 2011 | pre_2018 | 7 | 130,894 |
| 2011 | pre_2018 | 8 | 55,049 |
| 2012 | pre_2018 | 1 | 9,783,966 |
| 2012 | pre_2018 | 2 | 710,706 |
| 2012 | pre_2018 | 3 | 2,761,964 |
| 2012 | pre_2018 | 4 | 1,529,647 |
| 2012 | pre_2018 | 5 | 524,369 |
| 2012 | pre_2018 | 6 | 3,167,577 |
| 2012 | pre_2018 | 7 | 148,733 |
| 2012 | pre_2018 | 8 | 64,589 |
| 2013 | pre_2018 | 1 | 8,706,657 |
| 2013 | pre_2018 | 2 | 740,856 |
| 2013 | pre_2018 | 3 | 2,649,931 |
| 2013 | pre_2018 | 4 | 1,345,371 |
| 2013 | pre_2018 | 5 | 544,355 |
| 2013 | pre_2018 | 6 | 2,794,414 |
| 2013 | pre_2018 | 7 | 162,963 |
| 2013 | pre_2018 | 8 | 71,612 |
| 2014 | pre_2018 | 1 | 6,039,826 |
| 2014 | pre_2018 | 2 | 422,283 |
| 2014 | pre_2018 | 3 | 2,068,237 |
| 2014 | pre_2018 | 4 | 1,122,719 |
| 2014 | pre_2018 | 5 | 409,460 |
| 2014 | pre_2018 | 6 | 1,796,613 |
| 2014 | pre_2018 | 7 | 125,799 |
| 2014 | pre_2018 | 8 | 64,404 |
| 2015 | pre_2018 | 1 | 7,404,258 |
| 2015 | pre_2018 | 2 | 404,755 |
| 2015 | pre_2018 | 3 | 2,274,913 |
| 2015 | pre_2018 | 4 | 1,475,218 |
| 2015 | pre_2018 | 5 | 535,339 |
| 2015 | pre_2018 | 6 | 2,102,036 |
| 2015 | pre_2018 | 7 | 114,318 |
| 2015 | pre_2018 | 8 | 63,347 |
| 2016 | pre_2018 | 1 | 8,377,907 |
| 2016 | pre_2018 | 2 | 436,074 |
| 2016 | pre_2018 | 3 | 2,683,178 |
| 2016 | pre_2018 | 4 | 1,748,355 |
| 2016 | pre_2018 | 5 | 680,288 |
| 2016 | pre_2018 | 6 | 2,231,990 |
| 2016 | pre_2018 | 7 | 115,484 |
| 2016 | pre_2018 | 8 | 59,711 |
| 2017 | pre_2018 | 1 | 7,339,057 |
| 2017 | pre_2018 | 2 | 409,797 |
| 2017 | pre_2018 | 3 | 2,009,743 |
| 2017 | pre_2018 | 4 | 1,696,289 |
| 2017 | pre_2018 | 5 | 601,148 |
| 2017 | pre_2018 | 6 | 2,086,676 |
| 2017 | pre_2018 | 7 | 106,680 |
| 2017 | pre_2018 | 8 | 36,106 |
| 2018 | post_2018 | -1 | 1,961 |
| 2018 | post_2018 | 1 | 7,732,289 |
| 2018 | post_2018 | 2 | 338,822 |
| 2018 | post_2018 | 3 | 2,552,640 |
| 2018 | post_2018 | 4 | 1,771,582 |
| 2018 | post_2018 | 5 | 554,481 |
| 2018 | post_2018 | 6 | 2,012,221 |
| 2018 | post_2018 | 7 | 101,772 |
| 2018 | post_2018 | 8 | 74,703 |
| 2019 | post_2018 | -1 | 21 |
| 2019 | post_2018 | 1 | 9,344,813 |
| 2019 | post_2018 | 2 | 401,762 |
| 2019 | post_2018 | 3 | 2,536,776 |
| 2019 | post_2018 | 4 | 2,146,690 |
| 2019 | post_2018 | 5 | 720,712 |
| 2019 | post_2018 | 6 | 2,272,958 |
| 2019 | post_2018 | 7 | 76,609 |
| 2019 | post_2018 | 8 | 73,643 |
| 2020 | post_2018 | 1 | 14,637,334 |
| 2020 | post_2018 | 2 | 660,757 |
| 2020 | post_2018 | 3 | 2,886,263 |
| 2020 | post_2018 | 4 | 3,360,047 |
| 2020 | post_2018 | 5 | 1,248,380 |
| 2020 | post_2018 | 6 | 2,778,730 |
| 2020 | post_2018 | 7 | 57,561 |
| 2020 | post_2018 | 8 | 69,971 |
| 2021 | post_2018 | 1 | 15,091,528 |
| 2021 | post_2018 | 2 | 633,595 |
| 2021 | post_2018 | 3 | 2,950,191 |
| 2021 | post_2018 | 4 | 3,341,816 |
| 2021 | post_2018 | 5 | 1,404,858 |
| 2021 | post_2018 | 6 | 2,700,264 |
| 2021 | post_2018 | 7 | 52,773 |
| 2021 | post_2018 | 8 | 94,955 |
| 2022 | post_2018 | 1 | 8,416,071 |
| 2022 | post_2018 | 2 | 420,518 |
| 2022 | post_2018 | 3 | 2,525,024 |
| 2022 | post_2018 | 4 | 2,233,245 |
| 2022 | post_2018 | 5 | 747,635 |
| 2022 | post_2018 | 6 | 1,572,452 |
| 2022 | post_2018 | 7 | 74,275 |
| 2022 | post_2018 | 8 | 136,755 |
| 2023 | post_2018 | 1 | 5,710,399 |
| 2023 | post_2018 | 2 | 310,898 |
| 2023 | post_2018 | 3 | 2,037,094 |
| 2023 | post_2018 | 4 | 1,468,108 |
| 2023 | post_2018 | 5 | 536,137 |
| 2023 | post_2018 | 6 | 1,263,097 |
| 2023 | post_2018 | 7 | 62,622 |
| 2023 | post_2018 | 8 | 175,823 |
| 2024 | post_2018 | 1 | 6,197,085 |
| 2024 | post_2018 | 2 | 361,232 |
| 2024 | post_2018 | 3 | 2,103,462 |
| 2024 | post_2018 | 4 | 1,538,273 |
| 2024 | post_2018 | 5 | 581,940 |
| 2024 | post_2018 | 6 | 1,276,504 |
| 2024 | post_2018 | 7 | 47,312 |
| 2024 | post_2018 | 8 | 153,391 |

## Readiness Notes

- `county_year_lending` passes grain uniqueness and non-null key checks.
- County-level aggregate record totals reconcile to `loan_years_geo` rows with usable `county_fips_5`.
- Lender IDs are available for all years, but name fields are not present in the current canonical view.
- Fintech classification should therefore start from `lender_id` plus an external or separately sourced lender-name/classification crosswalk.
