# County-Year Lending Aggregate

## Scope

This step creates the first county-year lending aggregate from `loan_years_geo`. It does not classify fintech lenders, delete raw files, delete Parquet files, or create final research-specific aggregates.

## Source And Grain

- Source view: `loan_years_geo`
- Grain: `activity_year`, `state_fips_2`, `county_fips_5`
- Exclusion rule: rows with null `county_fips_5` are excluded from `county_year_lending` and summarized separately in `county_year_lending_missing_geo_qa`.

## Objects Created

| table_name | table_type |
| --- | --- |
| action_taken_metadata | BASE TABLE |
| county_year_lending | BASE TABLE |
| county_year_lending_missing_geo_qa | BASE TABLE |

## Metrics

- `total_records`: count of loan-level HMDA records at the county-year grain.
- `application_records`: count of non-purchase action records with `action_taken` in `1`, `2`, `3`, `4`, `5`, `7`, or `8`.
- `purchased_loans`: rows where `action_taken = '6'`.
- `total_applications`: legacy alias for `total_records`, retained for backward compatibility with the first public export.
- `originated_loans`: rows where `action_taken = '1'`.
- `denied_applications`: rows where `action_taken = '3'`.
- `total_loan_amount`: sum of normalized `loan_amount`.
- `average_loan_amount`: average of normalized `loan_amount`.
- `median_loan_amount`: DuckDB `MEDIAN(loan_amount)`.
- `lender_count`: distinct non-empty `lender_id`.

## Action Taken Mapping

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

## Aggregate Summary

- Aggregate row count: `58,006`
- Years: `2007-2024`
- Included records: `305,141,850`
- Application records: `259,119,806`
- Purchased loans: `46,022,044`
- Included applications legacy field: `305,141,850`
- Originated loans: `155,554,418`
- Denied applications: `48,614,948`

## County Count By Year

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

## Geography Consistency QA

Because the aggregate grain includes both `state_fips_2` and `county_fips_5`, the aggregate row count can exceed the distinct `county_fips_5` count when source geography has a null state or a state/county prefix mismatch. These rows are retained in the first aggregate for transparency and should be reviewed before research use.

| activity_year | aggregate_rows | distinct_county_fips_5 | rows_with_null_state_fips_2 | state_county_prefix_mismatches |
| --- | --- | --- | --- | --- |
| 2007 | 3,218 | 3,218 | 0 | 0 |
| 2008 | 3,219 | 3,219 | 0 | 0 |
| 2009 | 3,218 | 3,218 | 0 | 0 |
| 2010 | 3,218 | 3,218 | 0 | 0 |
| 2011 | 3,219 | 3,219 | 0 | 0 |
| 2012 | 3,220 | 3,220 | 0 | 0 |
| 2013 | 3,220 | 3,220 | 0 | 0 |
| 2014 | 3,218 | 3,218 | 0 | 0 |
| 2015 | 3,217 | 3,217 | 0 | 0 |
| 2016 | 3,219 | 3,219 | 0 | 0 |
| 2017 | 3,220 | 3,220 | 0 | 0 |
| 2018 | 3,261 | 3,261 | 0 | 0 |
| 2019 | 3,223 | 3,223 | 0 | 0 |
| 2020 | 3,222 | 3,222 | 0 | 0 |
| 2021 | 3,223 | 3,223 | 0 | 0 |
| 2022 | 3,224 | 3,224 | 0 | 0 |
| 2023 | 3,224 | 3,224 | 0 | 0 |
| 2024 | 3,223 | 3,223 | 0 | 0 |

## Missing Geography Exclusions

| activity_year | missing_geo_rows | missing_state_fips_2 | missing_county_fips_5 | lender_count | total_loan_amount |
| --- | --- | --- | --- | --- | --- |
| 2007 | 795,010 | 688,847 | 795,010 | 2,847 | 132,307,534,000 |
| 2008 | 641,620 | 583,515 | 641,620 | 2,751 | 95,375,690,000 |
| 2009 | 589,220 | 522,447 | 589,220 | 2,620 | 89,256,259,000 |
| 2010 | 371,488 | 322,927 | 371,488 | 2,309 | 56,182,516,000 |
| 2011 | 327,118 | 284,929 | 327,118 | 2,119 | 55,915,989,000 |
| 2012 | 352,923 | 315,703 | 352,923 | 1,994 | 64,614,505,000 |
| 2013 | 348,777 | 313,637 | 348,777 | 1,936 | 68,130,143,000 |
| 2014 | 320,233 | 264,330 | 320,233 | 1,844 | 63,134,749,000 |
| 2015 | 298,520 | 266,009 | 298,520 | 1,827 | 59,400,316,000 |
| 2016 | 277,748 | 254,571 | 277,748 | 1,736 | 64,798,813,000 |
| 2017 | 245,597 | 197,158 | 245,597 | 1,410 | 53,935,608,000 |
| 2018 | 359,902 | 193,005 | 359,902 | 2,088 | 88,764,820,000 |
| 2019 | 345,402 | 178,457 | 345,402 | 1,986 | 87,562,700,000 |
| 2020 | 301,904 | 186,151 | 301,904 | 1,695 | 324,366,190,000 |
| 2021 | 298,805 | 168,318 | 298,805 | 1,673 | 105,201,705,000 |
| 2022 | 445,296 | 193,094 | 445,296 | 1,562 | 160,716,610,000 |
| 2023 | 337,673 | 242,423 | 337,673 | 1,704 | 362,929,965,000 |
| 2024 | 296,190 | 208,661 | 296,190 | 1,559 | 113,989,740,000 |

## Notes

- `county_year_lending` is the first geography-normalized aggregate and should be QAed before adding fintech lender classifications.
- The preferred denominator for application-style rates is `application_records`; `total_records` also includes purchased-loan records.
- Missing-geography rows are not discarded silently; they are tracked in `county_year_lending_missing_geo_qa`.
- Action code `7` is documented as a preapproval denial but is not included in `denied_applications`, which uses application denial code `3`.
- Historic respondent IDs and post-2018 LEIs remain different identifier systems, so `lender_count` is useful within-year but not a cross-era lender identity resolution.
