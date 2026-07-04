# Geography Normalization

## Scope

This step adds normalized geography fields to `data/duckdb/hmda_panel.duckdb`. It does not create final research aggregates, classify fintech lenders, delete raw files, or delete Parquet files.

## Objects Created

| table_name | table_type |
| --- | --- |
| loan_years_geo | VIEW |
| state_fips_crosswalk | BASE TABLE |

## Current Raw Geography Formats

| activity_year | source_era | row_count | distinct_state_values | distinct_county_values | state_numeric_1_2 | state_alpha_2 | state_missing_or_na | county_numeric_1_3 | county_numeric_5 | county_missing_or_na |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | pre_2018 | 26,605,695 | 53 | 326 | 25,916,848 | 688,847 | 688,847 | 25,810,685 | 0 | 795,010 |
| 2008 | pre_2018 | 17,391,570 | 53 | 326 | 16,808,055 | 583,515 | 583,515 | 16,749,950 | 0 | 641,620 |
| 2009 | pre_2018 | 19,493,491 | 53 | 326 | 18,971,044 | 522,447 | 522,447 | 18,904,271 | 0 | 589,220 |
| 2010 | pre_2018 | 16,348,557 | 53 | 326 | 16,025,630 | 322,927 | 322,927 | 15,977,069 | 0 | 371,488 |
| 2011 | pre_2018 | 14,873,415 | 53 | 326 | 14,588,486 | 284,929 | 284,929 | 14,546,297 | 0 | 327,118 |
| 2012 | pre_2018 | 18,691,551 | 53 | 326 | 18,375,848 | 315,703 | 315,703 | 18,338,628 | 0 | 352,923 |
| 2013 | pre_2018 | 17,016,159 | 53 | 326 | 16,702,522 | 313,637 | 313,637 | 16,667,382 | 0 | 348,777 |
| 2014 | pre_2018 | 12,049,341 | 52 | 325 | 11,785,011 | 0 | 264,330 | 11,729,108 | 0 | 320,233 |
| 2015 | pre_2018 | 14,374,184 | 53 | 325 | 14,108,175 | 266,009 | 266,009 | 14,075,664 | 0 | 298,520 |
| 2016 | pre_2018 | 16,332,987 | 53 | 326 | 16,078,416 | 254,571 | 254,571 | 16,055,239 | 0 | 277,748 |
| 2017 | pre_2018 | 14,285,496 | 54 | 328 | 14,088,338 | 197,158 | 197,158 | 14,039,899 | 0 | 245,597 |
| 2018 | post_2018 | 15,140,471 | 57 | 3,310 | 0 | 15,138,510 | 203,813 | 0 | 14,781,034 | 359,432 |
| 2019 | post_2018 | 17,573,984 | 55 | 3,224 | 0 | 17,573,963 | 187,160 | 0 | 17,228,582 | 345,402 |
| 2020 | post_2018 | 25,699,043 | 57 | 3,223 | 0 | 25,699,043 | 191,662 | 0 | 25,397,139 | 301,904 |
| 2021 | post_2018 | 26,269,980 | 56 | 3,224 | 0 | 26,269,980 | 171,739 | 0 | 25,971,175 | 298,805 |
| 2022 | post_2018 | 16,125,975 | 56 | 3,225 | 0 | 16,125,975 | 196,096 | 0 | 15,680,679 | 445,296 |
| 2023 | post_2018 | 11,564,178 | 56 | 3,225 | 0 | 11,564,178 | 245,582 | 0 | 11,226,505 | 337,673 |
| 2024 | post_2018 | 12,259,199 | 55 | 3,224 | 0 | 12,259,199 | 215,946 | 0 | 11,963,009 | 296,190 |

## Mapping Rules

- If `state_code` is one or two numeric characters, left-pad it to two characters as `state_fips_2`.
- If `state_code` is a two-letter abbreviation, map it through `state_fips_crosswalk`.
- For post-2018 records with a valid five-digit `county_code`, derive `county_fips_5` directly from `county_code`.
- For post-2018 records with a valid five-digit `county_code`, derive `state_fips_2` from the first two digits of `county_code` when `state_code` is missing, unmapped, or conflicts with the county prefix.
- If `county_code` is one to three numeric characters, left-pad it to three characters as `county_fips_3` and combine with `state_fips_2` for `county_fips_5`.
- A five-digit `county_code` is treated as valid for this pass when its first two digits match the internal state/territory FIPS crosswalk and its county suffix is not `000`.
- Original `state_code` and `county_code` are preserved in `loan_years_geo`.
- `state_fips_2_source`, `state_fips_2_from_county_prefix`, `county_fips_5_source`, and `county_fips_5_valid_state_prefix` document how normalized values were produced.

## Validation Totals

| row_count | missing_state_fips_2 | missing_county_fips_5 | county_present_state_missing | state_county_prefix_mismatches | state_from_county_prefix_rows | distinct_states_normalized | distinct_counties_normalized |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 312,095,276 | 5,384,182 | 6,953,426 | 0 | 0 | 49,863 | 56 | 3,284 |

## Validation By Year

| activity_year | row_count | missing_state_fips_2 | missing_county_fips_5 | county_present_state_missing | state_county_prefix_mismatches | state_from_county_prefix_rows | distinct_states_normalized | distinct_counties_normalized |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 26,605,695 | 688,847 | 795,010 | 0 | 0 | 0 | 52 | 3,218 |
| 2008 | 17,391,570 | 583,515 | 641,620 | 0 | 0 | 0 | 52 | 3,219 |
| 2009 | 19,493,491 | 522,447 | 589,220 | 0 | 0 | 0 | 52 | 3,218 |
| 2010 | 16,348,557 | 322,927 | 371,488 | 0 | 0 | 0 | 52 | 3,218 |
| 2011 | 14,873,415 | 284,929 | 327,118 | 0 | 0 | 0 | 52 | 3,219 |
| 2012 | 18,691,551 | 315,703 | 352,923 | 0 | 0 | 0 | 52 | 3,220 |
| 2013 | 17,016,159 | 313,637 | 348,777 | 0 | 0 | 0 | 52 | 3,220 |
| 2014 | 12,049,341 | 264,330 | 320,233 | 0 | 0 | 0 | 52 | 3,218 |
| 2015 | 14,374,184 | 266,009 | 298,520 | 0 | 0 | 0 | 52 | 3,217 |
| 2016 | 16,332,987 | 254,571 | 277,748 | 0 | 0 | 0 | 52 | 3,219 |
| 2017 | 14,285,496 | 197,158 | 245,597 | 0 | 0 | 0 | 53 | 3,220 |
| 2018 | 15,140,471 | 193,005 | 359,902 | 0 | 0 | 17,829 | 55 | 3,261 |
| 2019 | 17,573,984 | 178,457 | 345,402 | 0 | 0 | 9,653 | 54 | 3,223 |
| 2020 | 25,699,043 | 186,151 | 301,904 | 0 | 0 | 5,513 | 55 | 3,222 |
| 2021 | 26,269,980 | 168,318 | 298,805 | 0 | 0 | 3,421 | 55 | 3,223 |
| 2022 | 16,125,975 | 193,094 | 445,296 | 0 | 0 | 3,002 | 55 | 3,224 |
| 2023 | 11,564,178 | 242,423 | 337,673 | 0 | 0 | 3,160 | 54 | 3,224 |
| 2024 | 12,259,199 | 208,661 | 296,190 | 0 | 0 | 7,285 | 54 | 3,223 |

## Source Flag Counts

| activity_year | source_era | state_fips_2_source | county_fips_5_source | row_count |
| --- | --- | --- | --- | --- |
| 2007 | pre_2018 | state_code_numeric | state_county_components | 25,810,685 |
| 2007 | pre_2018 | missing_state_code | missing_county_code | 688,847 |
| 2007 | pre_2018 | state_code_numeric | missing_county_code | 106,163 |
| 2008 | pre_2018 | state_code_numeric | state_county_components | 16,749,950 |
| 2008 | pre_2018 | missing_state_code | missing_county_code | 583,515 |
| 2008 | pre_2018 | state_code_numeric | missing_county_code | 58,105 |
| 2009 | pre_2018 | state_code_numeric | state_county_components | 18,904,271 |
| 2009 | pre_2018 | missing_state_code | missing_county_code | 522,447 |
| 2009 | pre_2018 | state_code_numeric | missing_county_code | 66,773 |
| 2010 | pre_2018 | state_code_numeric | state_county_components | 15,977,069 |
| 2010 | pre_2018 | missing_state_code | missing_county_code | 322,927 |
| 2010 | pre_2018 | state_code_numeric | missing_county_code | 48,561 |
| 2011 | pre_2018 | state_code_numeric | state_county_components | 14,546,297 |
| 2011 | pre_2018 | missing_state_code | missing_county_code | 284,929 |
| 2011 | pre_2018 | state_code_numeric | missing_county_code | 42,189 |
| 2012 | pre_2018 | state_code_numeric | state_county_components | 18,338,628 |
| 2012 | pre_2018 | missing_state_code | missing_county_code | 315,703 |
| 2012 | pre_2018 | state_code_numeric | missing_county_code | 37,220 |
| 2013 | pre_2018 | state_code_numeric | state_county_components | 16,667,382 |
| 2013 | pre_2018 | missing_state_code | missing_county_code | 313,637 |
| 2013 | pre_2018 | state_code_numeric | missing_county_code | 35,140 |
| 2014 | pre_2018 | state_code_numeric | state_county_components | 11,729,108 |
| 2014 | pre_2018 | missing_state_code | missing_county_code | 264,330 |
| 2014 | pre_2018 | state_code_numeric | missing_county_code | 55,903 |
| 2015 | pre_2018 | state_code_numeric | state_county_components | 14,075,664 |
| 2015 | pre_2018 | missing_state_code | missing_county_code | 266,009 |
| 2015 | pre_2018 | state_code_numeric | missing_county_code | 32,511 |
| 2016 | pre_2018 | state_code_numeric | state_county_components | 16,055,239 |
| 2016 | pre_2018 | missing_state_code | missing_county_code | 254,571 |
| 2016 | pre_2018 | state_code_numeric | missing_county_code | 23,177 |
| 2017 | pre_2018 | state_code_numeric | state_county_components | 14,039,899 |
| 2017 | pre_2018 | missing_state_code | missing_county_code | 197,158 |
| 2017 | pre_2018 | state_code_numeric | missing_county_code | 48,439 |
| 2018 | post_2018 | state_code_abbr | county_code_5 | 14,762,740 |
| 2018 | post_2018 | missing_state_code | missing_county_code | 193,000 |
| 2018 | post_2018 | state_code_abbr | missing_county_code | 166,432 |
| 2018 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 10,809 |
| 2018 | post_2018 | county_code_prefix_conflict_with_state_code | county_code_5 | 7,020 |
| 2018 | post_2018 | state_code_abbr | invalid_county_code_5 | 465 |
| 2018 | post_2018 | missing_state_code | unmapped_county_code | 5 |
| 2019 | post_2018 | state_code_abbr | county_code_5 | 17,218,929 |
| 2019 | post_2018 | missing_state_code | missing_county_code | 178,457 |
| 2019 | post_2018 | state_code_abbr | missing_county_code | 166,945 |
| 2019 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 8,703 |
| 2019 | post_2018 | county_code_prefix_conflict_with_state_code | county_code_5 | 950 |
| 2020 | post_2018 | state_code_abbr | county_code_5 | 25,391,626 |
| 2020 | post_2018 | missing_state_code | missing_county_code | 186,149 |
| 2020 | post_2018 | state_code_abbr | missing_county_code | 115,753 |
| 2020 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 5,513 |
| 2020 | post_2018 | unmapped_state_code_abbr | missing_county_code | 2 |
| 2021 | post_2018 | state_code_abbr | county_code_5 | 25,967,754 |
| 2021 | post_2018 | missing_state_code | missing_county_code | 168,318 |
| 2021 | post_2018 | state_code_abbr | missing_county_code | 130,487 |
| 2021 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 3,421 |
| 2022 | post_2018 | state_code_abbr | county_code_5 | 15,677,677 |
| 2022 | post_2018 | state_code_abbr | missing_county_code | 252,202 |
| 2022 | post_2018 | missing_state_code | missing_county_code | 193,094 |
| 2022 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 3,002 |
| 2023 | post_2018 | state_code_abbr | county_code_5 | 11,223,345 |
| 2023 | post_2018 | missing_state_code | missing_county_code | 242,422 |
| 2023 | post_2018 | state_code_abbr | missing_county_code | 95,250 |
| 2023 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 3,160 |
| 2023 | post_2018 | unmapped_state_code_abbr | missing_county_code | 1 |
| 2024 | post_2018 | state_code_abbr | county_code_5 | 11,955,724 |
| 2024 | post_2018 | missing_state_code | missing_county_code | 208,661 |
| 2024 | post_2018 | state_code_abbr | missing_county_code | 87,529 |
| 2024 | post_2018 | county_code_prefix_missing_or_unmapped_state_code | county_code_5 | 7,285 |

## Examples Of Unmapped Records

| activity_year | source_era | state_code | county_code | state_fips_2 | state_fips_2_source | state_fips_2_from_county_prefix | county_fips_3 | county_fips_5 | county_fips_5_source | county_fips_5_valid_state_prefix | row_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 688,847 |
| 2008 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 583,515 |
| 2009 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 522,447 |
| 2010 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 322,927 |
| 2012 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 315,703 |
| 2013 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 313,637 |
| 2011 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 284,929 |
| 2015 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 266,009 |
| 2014 | pre_2018 | None | None | None | missing_state_code | False | None | None | missing_county_code | False | 264,330 |
| 2016 | pre_2018 | NA | NA  | None | missing_state_code | False | None | None | missing_county_code | False | 254,571 |
| 2023 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 242,422 |
| 2024 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 208,661 |
| 2017 | pre_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 197,158 |
| 2022 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 193,094 |
| 2018 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 191,029 |
| 2020 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 186,149 |
| 2019 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 178,436 |
| 2021 | post_2018 | NA | NA | None | missing_state_code | False | None | None | missing_county_code | False | 168,318 |
| 2022 | post_2018 | TX | NA | 48 | state_code_abbr | False | None | None | missing_county_code | False | 47,344 |
| 2022 | post_2018 | CA | NA | 06 | state_code_abbr | False | None | None | missing_county_code | False | 26,549 |
| 2022 | post_2018 | FL | NA | 12 | state_code_abbr | False | None | None | missing_county_code | False | 23,279 |
| 2019 | post_2018 | TX | NA | 48 | state_code_abbr | False | None | None | missing_county_code | False | 19,600 |
| 2019 | post_2018 | CA | NA | 06 | state_code_abbr | False | None | None | missing_county_code | False | 18,581 |
| 2018 | post_2018 | TX | NA | 48 | state_code_abbr | False | None | None | missing_county_code | False | 17,918 |
| 2021 | post_2018 | CA | NA | 06 | state_code_abbr | False | None | None | missing_county_code | False | 16,502 |
| 2018 | post_2018 | CA | NA | 06 | state_code_abbr | False | None | None | missing_county_code | False | 16,132 |
| 2020 | post_2018 | CA | NA | 06 | state_code_abbr | False | None | None | missing_county_code | False | 14,374 |
| 2023 | post_2018 | TX | NA | 48 | state_code_abbr | False | None | None | missing_county_code | False | 13,037 |
| 2020 | post_2018 | TX | NA | 48 | state_code_abbr | False | None | None | missing_county_code | False | 12,468 |
| 2007 | pre_2018 | 48 | NA  | 48 | state_code_numeric | False | None | None | missing_county_code | False | 12,045 |

## Sample Successful Mappings

| activity_year | source_era | state_code | county_code | state_fips_2 | state_fips_2_source | state_fips_2_from_county_prefix | county_fips_3 | county_fips_5 | county_fips_5_source | county_fips_5_valid_state_prefix | row_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | pre_2018 | 06 | 037 | 06 | state_code_numeric | False | 037 | 06037 | state_county_components | False | 780,256 |
| 2007 | pre_2018 | 04 | 013 | 04 | state_code_numeric | False | 013 | 04013 | state_county_components | False | 523,747 |
| 2007 | pre_2018 | 17 | 031 | 17 | state_code_numeric | False | 031 | 17031 | state_county_components | False | 514,892 |
| 2007 | pre_2018 | 06 | 065 | 06 | state_code_numeric | False | 065 | 06065 | state_county_components | False | 300,968 |
| 2007 | pre_2018 | 48 | 201 | 48 | state_code_numeric | False | 201 | 48201 | state_county_components | False | 285,130 |
| 2007 | pre_2018 | 06 | 073 | 06 | state_code_numeric | False | 073 | 06073 | state_county_components | False | 272,129 |
| 2007 | pre_2018 | 12 | 086 | 12 | state_code_numeric | False | 086 | 12086 | state_county_components | False | 263,114 |
| 2007 | pre_2018 | 06 | 071 | 06 | state_code_numeric | False | 071 | 06071 | state_county_components | False | 260,415 |
| 2007 | pre_2018 | 32 | 003 | 32 | state_code_numeric | False | 003 | 32003 | state_county_components | False | 250,972 |
| 2007 | pre_2018 | 06 | 059 | 06 | state_code_numeric | False | 059 | 06059 | state_county_components | False | 237,395 |
| 2007 | pre_2018 | 12 | 011 | 12 | state_code_numeric | False | 011 | 12011 | state_county_components | False | 202,999 |
| 2007 | pre_2018 | 53 | 033 | 53 | state_code_numeric | False | 033 | 53033 | state_county_components | False | 202,391 |
| 2007 | pre_2018 | 26 | 163 | 26 | state_code_numeric | False | 163 | 26163 | state_county_components | False | 161,860 |
| 2007 | pre_2018 | 48 | 113 | 48 | state_code_numeric | False | 113 | 48113 | state_county_components | False | 156,656 |
| 2007 | pre_2018 | 06 | 067 | 06 | state_code_numeric | False | 067 | 06067 | state_county_components | False | 148,295 |
| 2007 | pre_2018 | 06 | 085 | 06 | state_code_numeric | False | 085 | 06085 | state_county_components | False | 143,975 |
| 2007 | pre_2018 | 48 | 439 | 48 | state_code_numeric | False | 439 | 48439 | state_county_components | False | 141,978 |
| 2007 | pre_2018 | 24 | 033 | 24 | state_code_numeric | False | 033 | 24033 | state_county_components | False | 141,525 |
| 2007 | pre_2018 | 12 | 095 | 12 | state_code_numeric | False | 095 | 12095 | state_county_components | False | 137,812 |
| 2007 | pre_2018 | 42 | 101 | 42 | state_code_numeric | False | 101 | 42101 | state_county_components | False | 135,816 |
| 2007 | pre_2018 | 06 | 001 | 06 | state_code_numeric | False | 001 | 06001 | state_county_components | False | 132,931 |
| 2007 | pre_2018 | 12 | 099 | 12 | state_code_numeric | False | 099 | 12099 | state_county_components | False | 130,944 |
| 2007 | pre_2018 | 12 | 057 | 12 | state_code_numeric | False | 057 | 12057 | state_county_components | False | 128,036 |
| 2007 | pre_2018 | 48 | 029 | 48 | state_code_numeric | False | 029 | 48029 | state_county_components | False | 127,461 |
| 2007 | pre_2018 | 06 | 013 | 06 | state_code_numeric | False | 013 | 06013 | state_county_components | False | 122,059 |
| 2007 | pre_2018 | 49 | 035 | 49 | state_code_numeric | False | 035 | 49035 | state_county_components | False | 121,796 |
| 2007 | pre_2018 | 36 | 103 | 36 | state_code_numeric | False | 103 | 36103 | state_county_components | False | 119,892 |
| 2007 | pre_2018 | 13 | 121 | 13 | state_code_numeric | False | 121 | 13121 | state_county_components | False | 107,043 |
| 2007 | pre_2018 | 36 | 081 | 36 | state_code_numeric | False | 081 | 36081 | state_county_components | False | 106,680 |
| 2007 | pre_2018 | 37 | 119 | 37 | state_code_numeric | False | 119 | 37119 | state_county_components | False | 106,357 |
| 2007 | pre_2018 | 29 | 189 | 29 | state_code_numeric | False | 189 | 29189 | state_county_components | False | 105,837 |
| 2007 | pre_2018 | 26 | 125 | 26 | state_code_numeric | False | 125 | 26125 | state_county_components | False | 105,475 |
| 2007 | pre_2018 | 04 | 019 | 04 | state_code_numeric | False | 019 | 04019 | state_county_components | False | 104,851 |
| 2007 | pre_2018 | 25 | 017 | 25 | state_code_numeric | False | 017 | 25017 | state_county_components | False | 104,313 |
| 2007 | pre_2018 | 53 | 053 | 53 | state_code_numeric | False | 053 | 53053 | state_county_components | False | 103,179 |
| 2007 | pre_2018 | 12 | 031 | 12 | state_code_numeric | False | 031 | 12031 | state_county_components | False | 101,583 |
| 2007 | pre_2018 | 06 | 029 | 06 | state_code_numeric | False | 029 | 06029 | state_county_components | False | 93,389 |
| 2007 | pre_2018 | 51 | 059 | 51 | state_code_numeric | False | 059 | 51059 | state_county_components | False | 93,165 |
| 2007 | pre_2018 | 27 | 053 | 27 | state_code_numeric | False | 053 | 27053 | state_county_components | False | 92,372 |
| 2007 | pre_2018 | 53 | 061 | 53 | state_code_numeric | False | 061 | 53061 | state_county_components | False | 91,277 |

## Notes

- `loan_years_geo` is a view over `loan_years`; it does not duplicate the loan-level dataset.
- `state_fips_crosswalk` is an internal table containing US states, DC, and major territories present in HMDA-style data.
- Post-2018 rows with valid five-digit county FIPS values use the county prefix as the fallback or conflict-resolution source for `state_fips_2`.
- Remaining unmapped county records are primarily missing or `NA` county codes, plus records where the source county is not a usable FIPS component.
- County-year research aggregates should use `state_fips_2` and `county_fips_5`, not the raw `state_code` and `county_code` fields.
