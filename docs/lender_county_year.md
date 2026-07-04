# Lender-County-Year Aggregate

## Scope

This step creates the first lender-county-year aggregate from `loan_years_geo`. It does not classify fintech lenders and does not create `county_year_fintech_lending`.

## Source And Grain

- Source view: `loan_years_geo`
- Grain: `activity_year`, `state_fips_2`, `county_fips_5`, `lender_id`
- Main-table exclusion rule: rows with missing `county_fips_5` are excluded.
- Main-table exclusion rule: rows with missing or blank `lender_id` are excluded.
- Rows with missing lender IDs but usable county geography are summarized in `lender_county_year_missing_lender_qa`.
- Rows with missing county geography are summarized in `lender_county_year_missing_geo_qa`.

## Objects Created

| table_name | table_type |
| --- | --- |
| lender_county_year | BASE TABLE |
| lender_county_year_missing_geo_qa | BASE TABLE |
| lender_county_year_missing_lender_qa | BASE TABLE |

## Metrics

- `records`: count of loan-level HMDA records at the lender-county-year grain.
- `application_records`: count of non-purchase action records with `action_taken` in `1`, `2`, `3`, `4`, `5`, `7`, or `8`.
- `purchased_loans`: rows where `action_taken = '6'`.
- `applications`: legacy alias for `records`, retained for backward compatibility with the first public export.
- `originated_loans`: rows where `action_taken = '1'`.
- `denied_applications`: rows where `action_taken = '3'`.
- `total_loan_amount`: sum of normalized `loan_amount`.
- `average_loan_amount`: average of normalized `loan_amount`.
- `median_loan_amount`: DuckDB `MEDIAN(loan_amount)`.
- `loan_type_1_count` through `loan_type_4_count`, plus `loan_type_other_count`.
- `loan_purpose_1_count`, `loan_purpose_2_count`, `loan_purpose_3_count`, `loan_purpose_31_count`, `loan_purpose_32_count`, `loan_purpose_4_count`, `loan_purpose_5_count`, plus `loan_purpose_other_count`.

## Summary

- Row count: `8,923,506`
- Years: `2007-2024`
- Records: `305,141,850`
- Application records: `259,119,806`
- Purchased loans: `46,022,044`
- Applications legacy field: `305,141,850`
- Originated loans: `155,554,418`
- Denied applications: `48,614,948`
- Total loan amount: `75,734,874,727,000`

## Key And Grain Checks

| null_activity_year | null_state_fips_2 | null_county_fips_5 | null_or_blank_lender_id |
| --- | --- | --- | --- |
| 0 | 0 | 0 | 0 |

| duplicate_grain_rows |
| --- |
| 0 |

## Lender-County-Year Counts By Year

| activity_year | lender_county_rows | county_count | lender_count | records | application_records | purchased_loans | applications | originated_loans | denied_applications | total_loan_amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 563,296 | 3,218 | 8,335 | 25,810,685 | 21,072,710 | 4,737,975 | 25,810,685 | 10,363,770 | 5,819,928 | 5,146,875,752,000 |
| 2008 | 470,810 | 3,219 | 8,118 | 16,749,950 | 13,849,145 | 2,900,805 | 16,749,950 | 7,092,935 | 3,789,609 | 3,350,860,801,000 |
| 2009 | 453,382 | 3,218 | 7,872 | 18,904,271 | 14,626,912 | 4,277,359 | 18,904,271 | 8,839,646 | 2,870,671 | 3,812,953,809,000 |
| 2010 | 410,419 | 3,218 | 7,683 | 15,977,069 | 12,756,506 | 3,220,563 | 15,977,069 | 7,810,204 | 2,482,053 | 3,313,976,640,000 |
| 2011 | 410,564 | 3,219 | 7,477 | 14,546,297 | 11,610,525 | 2,935,772 | 14,546,297 | 7,056,938 | 2,308,251 | 2,992,138,358,000 |
| 2012 | 449,912 | 3,220 | 7,250 | 18,338,628 | 15,174,893 | 3,163,735 | 18,338,628 | 9,739,921 | 2,718,055 | 3,872,898,552,000 |
| 2013 | 455,729 | 3,220 | 7,053 | 16,667,382 | 13,875,206 | 2,792,176 | 16,667,382 | 8,678,842 | 2,607,088 | 3,786,987,064,000 |
| 2014 | 435,891 | 3,218 | 6,925 | 11,729,108 | 9,934,128 | 1,794,980 | 11,729,108 | 6,019,168 | 2,018,466 | 2,536,226,723,000 |
| 2015 | 465,895 | 3,217 | 6,787 | 14,075,664 | 11,975,714 | 2,099,950 | 14,075,664 | 7,383,304 | 2,232,849 | 3,297,102,667,000 |
| 2016 | 491,666 | 3,219 | 6,640 | 16,055,239 | 13,826,628 | 2,228,611 | 16,055,239 | 8,358,154 | 2,645,324 | 3,939,731,541,000 |
| 2017 | 496,209 | 3,220 | 5,758 | 14,039,899 | 11,955,535 | 2,084,364 | 14,039,899 | 7,324,077 | 1,971,050 | 3,488,812,000,000 |
| 2018 | 504,818 | 3,261 | 5,667 | 14,780,569 | 12,770,422 | 2,010,147 | 14,780,569 | 7,697,135 | 2,479,327 | 3,535,319,885,000 |
| 2019 | 527,478 | 3,223 | 5,525 | 17,228,582 | 14,958,693 | 2,269,889 | 17,228,582 | 9,308,852 | 2,462,341 | 4,618,373,140,000 |
| 2020 | 582,303 | 3,222 | 4,499 | 25,397,139 | 22,621,049 | 2,776,090 | 25,397,139 | 14,608,161 | 2,813,404 | 7,776,721,675,000 |
| 2021 | 615,122 | 3,223 | 4,349 | 25,971,175 | 23,273,062 | 2,698,113 | 25,971,175 | 15,047,525 | 2,900,186 | 7,885,035,955,000 |
| 2022 | 573,171 | 3,224 | 4,456 | 15,680,679 | 14,180,296 | 1,500,383 | 15,680,679 | 8,368,999 | 2,451,649 | 5,224,483,635,000 |
| 2023 | 506,792 | 3,224 | 5,085 | 11,226,505 | 9,971,284 | 1,255,221 | 11,226,505 | 5,686,639 | 1,991,157 | 3,404,933,745,000 |
| 2024 | 510,049 | 3,223 | 4,880 | 11,963,009 | 10,687,098 | 1,275,911 | 11,963,009 | 6,170,148 | 2,053,540 | 3,751,442,785,000 |

## Reconciliation

| activity_year | expected_main_rows | main_records | main_difference | expected_missing_lender_rows | qa_missing_lender_rows | missing_lender_difference | expected_missing_geo_rows | qa_missing_geo_rows | missing_geo_difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 25,810,685 | 25,810,685 | 0 | 0 | 0 | 0 | 795,010 | 795,010 | 0 |
| 2008 | 16,749,950 | 16,749,950 | 0 | 0 | 0 | 0 | 641,620 | 641,620 | 0 |
| 2009 | 18,904,271 | 18,904,271 | 0 | 0 | 0 | 0 | 589,220 | 589,220 | 0 |
| 2010 | 15,977,069 | 15,977,069 | 0 | 0 | 0 | 0 | 371,488 | 371,488 | 0 |
| 2011 | 14,546,297 | 14,546,297 | 0 | 0 | 0 | 0 | 327,118 | 327,118 | 0 |
| 2012 | 18,338,628 | 18,338,628 | 0 | 0 | 0 | 0 | 352,923 | 352,923 | 0 |
| 2013 | 16,667,382 | 16,667,382 | 0 | 0 | 0 | 0 | 348,777 | 348,777 | 0 |
| 2014 | 11,729,108 | 11,729,108 | 0 | 0 | 0 | 0 | 320,233 | 320,233 | 0 |
| 2015 | 14,075,664 | 14,075,664 | 0 | 0 | 0 | 0 | 298,520 | 298,520 | 0 |
| 2016 | 16,055,239 | 16,055,239 | 0 | 0 | 0 | 0 | 277,748 | 277,748 | 0 |
| 2017 | 14,039,899 | 14,039,899 | 0 | 0 | 0 | 0 | 245,597 | 245,597 | 0 |
| 2018 | 14,780,569 | 14,780,569 | 0 | 0 | 0 | 0 | 359,902 | 359,902 | 0 |
| 2019 | 17,228,582 | 17,228,582 | 0 | 0 | 0 | 0 | 345,402 | 345,402 | 0 |
| 2020 | 25,397,139 | 25,397,139 | 0 | 0 | 0 | 0 | 301,904 | 301,904 | 0 |
| 2021 | 25,971,175 | 25,971,175 | 0 | 0 | 0 | 0 | 298,805 | 298,805 | 0 |
| 2022 | 15,680,679 | 15,680,679 | 0 | 0 | 0 | 0 | 445,296 | 445,296 | 0 |
| 2023 | 11,226,505 | 11,226,505 | 0 | 0 | 0 | 0 | 337,673 | 337,673 | 0 |
| 2024 | 11,963,009 | 11,963,009 | 0 | 0 | 0 | 0 | 296,190 | 296,190 | 0 |

## Missing Lender QA

No rows with usable county geography and missing lender IDs were found.

## Missing Geography QA

| activity_year | missing_geo_rows | missing_state_fips_2 | missing_county_fips_5 | missing_lender_id | distinct_lenders | originated_loans | denied_applications | total_loan_amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 795,010 | 688,847 | 795,010 | 0 | 2,847 | 77,775 | 132,602 | 132,307,534,000 |
| 2008 | 641,620 | 583,515 | 641,620 | 0 | 2,751 | 84,327 | 154,993 | 95,375,690,000 |
| 2009 | 589,220 | 522,447 | 589,220 | 0 | 2,620 | 111,290 | 142,296 | 89,256,259,000 |
| 2010 | 371,488 | 322,927 | 371,488 | 0 | 2,309 | 53,133 | 74,736 | 56,182,516,000 |
| 2011 | 327,118 | 284,929 | 327,118 | 0 | 2,119 | 38,324 | 46,595 | 55,915,989,000 |
| 2012 | 352,923 | 315,703 | 352,923 | 0 | 1,994 | 44,045 | 43,909 | 64,614,505,000 |
| 2013 | 348,777 | 313,637 | 348,777 | 0 | 1,936 | 27,815 | 42,843 | 68,130,143,000 |
| 2014 | 320,233 | 264,330 | 320,233 | 0 | 1,844 | 20,658 | 49,771 | 63,134,749,000 |
| 2015 | 298,520 | 266,009 | 298,520 | 0 | 1,827 | 20,954 | 42,064 | 59,400,316,000 |
| 2016 | 277,748 | 254,571 | 277,748 | 0 | 1,736 | 19,753 | 37,854 | 64,798,813,000 |
| 2017 | 245,597 | 197,158 | 245,597 | 0 | 1,410 | 14,980 | 38,693 | 53,935,608,000 |
| 2018 | 359,902 | 193,005 | 359,902 | 1,961 | 2,088 | 35,154 | 73,313 | 88,764,820,000 |
| 2019 | 345,402 | 178,457 | 345,402 | 21 | 1,986 | 35,961 | 74,435 | 87,562,700,000 |
| 2020 | 301,904 | 186,151 | 301,904 | 0 | 1,695 | 29,173 | 72,859 | 324,366,190,000 |
| 2021 | 298,805 | 168,318 | 298,805 | 0 | 1,673 | 44,003 | 50,005 | 105,201,705,000 |
| 2022 | 445,296 | 193,094 | 445,296 | 0 | 1,562 | 47,072 | 73,375 | 160,716,610,000 |
| 2023 | 337,673 | 242,423 | 337,673 | 0 | 1,704 | 23,760 | 45,937 | 362,929,965,000 |
| 2024 | 296,190 | 208,661 | 296,190 | 0 | 1,559 | 26,937 | 49,922 | 113,989,740,000 |

## Notes

- `lender_county_year` is suitable for lender-level geography expansion analysis but does not identify fintech lenders.
- The preferred denominator for application-style rates is `application_records`; `records` also includes purchased-loan records.
- Historic respondent IDs and post-2018 LEIs remain different identifier systems; cross-era lender matching requires a separate crosswalk.
- The current canonical database does not include lender names.
