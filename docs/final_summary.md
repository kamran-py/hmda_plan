# Final Research Project Summary

## 1. Executive Summary

This project built a reproducible HMDA data engineering pipeline for mortgage-lending analysis over 2007-2024. The pipeline starts from public HMDA loan-level files, converts annual raw files into Parquet, builds a DuckDB database, normalizes geography across the 2018 schema break, creates county-year and lender-county-year aggregates, and exports analysis-ready files.

HMDA is large and difficult to process because each annual file contains millions of loan-level application records. This run processed 312,095,276 loan-level rows across 18 years. Raw files totaled 51,723,943,287 bytes, while the annual Parquet intermediates totaled 7,328,201,304 bytes. The scale makes full-file pandas workflows inappropriate for the main pipeline. DuckDB and Parquet were used because they support large columnar scans, SQL aggregation, typed storage, resumable annual processing, and compact intermediate outputs.

The final research-ready tables are:

- `county_year_lending`: 58,006 county-year rows.
- `lender_county_year`: 8,923,506 lender-county-year rows.
- `loan_years_geo`: a geography-normalized loan-level view over 312,095,276 rows.

The current dataset can support descriptive county-year lending trends, county-level lending volumes, lender market presence by county, lender-county-year panel construction, and preparatory work for entry/exit or geographic expansion analysis.

The current dataset does not yet support definitive fintech classification. Explicit lender-name fields are not available in the constructed canonical data, and no lender-name or lender-classification crosswalk has been added. Fintech lender shares, fintech entry, and fintech-specific causal analysis require external lender identity enrichment before they can be computed credibly.

## 2. Research Objective

The substantive goal is to study the geographic expansion of mortgage lenders across US counties over time. The project prepares the panel structure needed for future analysis of fintech and nonbank lender expansion by constructing consistent county-year and lender-county-year data from HMDA loan-level records.

This project is a data-construction project, not a final causal analysis. It does not estimate treatment effects, classify lenders as fintech, or compute final fintech market shares. Its purpose is to create a reproducible foundation on which those later research steps can be built.

## 3. Data Sources And Coverage

The data source is public HMDA loan-level data covering 2007-2024.

Two source systems were used:

- Historic HMDA files for 2007-2017:
  `https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_{YEAR}_nationwide_all-records_codes.zip`
- HMDA Data Browser API files for 2018-2024:
  `https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years={YEAR}`

The raw download manifest contains 18 records, all with status `downloaded`. Total raw downloaded bytes were 51,723,943,287, about 48.17 GiB. Annual Parquet files were created for all 18 years and totaled 7,328,201,304 bytes, about 6.82 GiB. Conversion metadata contains 18 records, zero metadata errors, and 312,095,276 total loan-level rows.

| source era | years | raw format | canonical output format | schema issue |
| --- | --- | --- | --- | --- |
| pre_2018 | 2007-2017 | Zipped CSV files with historic LAR columns and numeric codes | Annual Parquet files plus canonical DuckDB view | Uses `as_of_year`, `respondent_id`, `loan_amount_000s`, `owner_occupancy`, numeric/FIPS-style state codes, and 1-3 digit county components. |
| post_2018 | 2018-2024 | CSV streams from the Data Browser API | Annual Parquet files plus canonical DuckDB view | Uses `activity_year`, `lei`, `loan_amount`, `occupancy_type`, two-letter state codes, and 5-digit county FIPS codes. |

Year-specific issues discovered during QA include:

- Missing county geography appears in every year and is excluded from county-level aggregates.
- The 2018 schema break changes both column names and lender identifier systems.
- Post-2018 records sometimes have valid five-digit county FIPS values with missing or conflicting `state_code`. The geography normalization was revised to derive `state_fips_2` from the county FIPS prefix for those records.
- Missing canonical lender IDs occur in 2018 for 1,961 rows and in 2019 for 21 rows. These rows are in the missing-geography bucket and are not excluded separately from the lender-county-year main table.

## 4. Pipeline Architecture And Design Principles

The actual pipeline is:

```text
raw HMDA source files
-> cached raw files
-> annual Parquet conversion
-> canonical DuckDB view/table
-> geography-normalized view
-> county-year and lender-county-year aggregates
-> export files
```

The current run used a raw-first design: all raw source files were downloaded into `data/raw` before conversion. This was simple and reproducible once approved, and it created a local source cache for repeated conversion and QA. It is not the preferred production architecture for large public datasets because it requires retaining large raw intermediates.

The preferred production design is year-at-a-time:

```text
source file or stream -> convert to Parquet -> validate -> optionally remove raw intermediate
```

That design reduces local storage pressure and makes the pipeline more operationally robust. Since the raw cache already exists for this run, later steps used cached-raw mode.

Parquet is the durable intermediate format because it is columnar, typed, compact, and efficient for repeated scans. DuckDB is used for large scans, schema inspection, conversion, aggregation, and export because it can query CSV, Parquet, and local database objects directly without loading full files into memory. Pandas is intentionally avoided for full raw HMDA files because the annual source files are too large for a conventional in-memory workflow.

## 5. Database Objects

The final DuckDB database is `data/duckdb/hmda_panel.duckdb`. Its file size is 337,129,472 bytes. The database is a generated local artifact and is not committed to GitHub; it depends on locally regenerated annual Parquet files because `loan_years` is a view over those files.

| object | type | row count | grain | key columns | purpose and intended use |
| --- | --- | ---: | --- | --- | --- |
| `loan_years` | VIEW | 312,095,276 | Loan-level HMDA record | `activity_year`, `lender_id`, `state_code`, `county_code` | Canonical loan-level view over annual Parquet files. Used as the base for normalization and QA. |
| `column_metadata` | BASE TABLE | 14 | Column metadata row | `column_name` | Documents canonical column names, source-era mappings, types, valid years, and notes. |
| `year_summary` | BASE TABLE | 18 | Year | `activity_year` | Year-level row counts, state counts, county counts, lender counts, and loan amount totals. |
| `state_fips_crosswalk` | BASE TABLE | 56 | State or territory | `state_fips`, `state_abbr` | Internal crosswalk for converting two-letter state abbreviations to two-digit FIPS codes. |
| `loan_years_geo` | VIEW | 312,095,276 | Loan-level HMDA record with normalized geography | `activity_year`, `state_fips_2`, `county_fips_5`, `lender_id` | Geography-normalized view used for all county-level and lender-county-level aggregates. |
| `county_year_lending` | BASE TABLE | 58,006 | County-year | `activity_year`, `state_fips_2`, `county_fips_5` | Main county-year aggregate for lending volumes, originations, denials, loan amounts, and lender counts. |
| `county_year_lending_missing_geo_qa` | BASE TABLE | 18 | Year | `activity_year` | Tracks loan-level rows excluded from county-year aggregates because `county_fips_5` is missing. |
| `action_taken_metadata` | BASE TABLE | 16 | Source era by action code | `source_era`, `action_taken` | Documents which HMDA action codes are counted as originations and denials. |
| `lender_county_year` | BASE TABLE | 8,923,506 | Lender-county-year | `activity_year`, `state_fips_2`, `county_fips_5`, `lender_id` | Main lender-county-year panel for lender presence and geographic expansion analysis. |
| `lender_county_year_missing_lender_qa` | BASE TABLE | 0 | County-year missing lender bucket | `activity_year`, `state_fips_2`, `county_fips_5` | Tracks rows with usable county geography but missing lender IDs. No such rows remain after the main exclusions. |
| `lender_county_year_missing_geo_qa` | BASE TABLE | 18 | Year | `activity_year` | Tracks rows excluded from lender-county-year analysis because county geography is missing. |
| `build_log` | BASE TABLE | 10 | Build log key-value row | `key` | Records database path, build timestamps, source Parquet files, created objects, years, and total rows. |

## 6. Unit Of Observation And Panel Structure

The source unit is one HMDA loan/application record as represented in the annual HMDA files.

The county-year aggregate unit is:

```text
activity_year x state_fips_2 x county_fips_5
```

This table supports county-level panel analysis of mortgage applications, originations, denials, total loan amounts, average loan amounts, median loan amounts, and lender counts.

The lender-county-year aggregate unit is:

```text
activity_year x state_fips_2 x county_fips_5 x lender_id
```

This table supports lender market presence analysis, lender entry and exit by county, geographic expansion analysis, and later fintech-share construction after lenders are externally classified. It is also the appropriate intermediate for building lender concentration, lender count, or lender mix measures at the county-year level.

## 7. Variable Construction

| variable | construction | pre/post-2018 differences | caveats |
| --- | --- | --- | --- |
| `activity_year` | Canonical activity year. | Pre-2018 uses `as_of_year`; post-2018 uses `activity_year`. | Stored as integer in the canonical view. |
| `source_era` | Assigned by year. | `pre_2018` for 2007-2017; `post_2018` for 2018-2024. | Used to separate schema eras. |
| `lender_id` | Canonical lender identifier. | Pre-2018 uses `respondent_id`; post-2018 uses `lei`. | These are not equivalent ID systems across the 2018 break. |
| `lender_id_type` | Identifier system label. | `respondent_id` before 2018; `lei` from 2018 onward. | Needed for lender continuity work. |
| `state_fips_2` | Normalized two-digit state FIPS. | Pre-2018 numeric/FIPS-style state codes are left-padded; post-2018 two-letter abbreviations are mapped through `state_fips_crosswalk`, with county-prefix fallback for valid five-digit county FIPS records. | Missing state remains when state and usable county geography are absent. |
| `county_fips_5` | Normalized five-digit county FIPS. | Pre-2018 combines state FIPS with 1-3 digit county components; post-2018 uses valid five-digit county codes directly. | Rows with missing county geography are excluded from county-level main aggregates. |
| `applications` / `total_applications` | Count of loan-level rows in the aggregate cell. | Same aggregation logic across eras after canonicalization. | Interpret as HMDA records under the action-code and coverage definitions of the source data. |
| `originated_loans` | Count where `action_taken = '1'`. | Same code used in both eras. | Depends on HMDA action-code consistency. |
| `denied_applications` | Count where `action_taken = '3'`. | Same code used in both eras. | Preapproval denial code `7` is documented but not included. |
| `total_loan_amount` | Sum of canonical `loan_amount`. | Pre-2018 `loan_amount_000s` is multiplied by 1,000; post-2018 `loan_amount` is cast directly. | Loan amount definitions should be checked before interpreting levels across eras. |
| `average_loan_amount` | Average of canonical `loan_amount`. | Same after canonicalization. | Sensitive to missing or nonstandard amount reporting. |
| `median_loan_amount` | DuckDB `MEDIAN(loan_amount)` within aggregate cell. | Same after canonicalization. | Computed in both county-year and lender-county-year aggregates. |
| `lender_count` | Distinct non-empty `lender_id` in county-year cells. | Counts respondent IDs before 2018 and LEIs after 2018. | Not a cross-era resolved lender count. |
| `raw_source_columns` | JSON with selected raw values used for canonical mappings. | Pre-2018 includes fields such as `as_of_year`, `respondent_id`, `loan_amount_000s`, `owner_occupancy`, `applicant_income_000s`, and `census_tract_number`; post-2018 includes fields such as `raw_activity_year`, `lei`, `loan_amount`, `occupancy_type`, `income`, and `census_tract`. | It is not the full raw source record. |

## 8. Geography Normalization

Raw geography fields were not directly comparable across eras. Before 2018, HMDA uses numeric/FIPS-style `state_code` values and county components that are typically 1-3 digits. From 2018 onward, the Data Browser files use two-letter state abbreviations and mostly five-digit county FIPS codes.

The final normalization rules are:

- If `state_code` is one or two numeric characters, left-pad it to two digits as `state_fips_2`.
- If `state_code` is a two-letter abbreviation, map it through `state_fips_crosswalk`.
- If `county_code` is one to three numeric characters, left-pad it to three digits as `county_fips_3` and combine it with `state_fips_2` to create `county_fips_5`.
- For post-2018 records with a valid five-digit `county_code`, derive `county_fips_5` directly from `county_code`.
- For post-2018 records with a valid five-digit `county_code`, derive `state_fips_2` from the first two digits of `county_code` when `state_code` is missing, unmapped, or conflicts with the county prefix.
- A five-digit `county_code` is treated as valid for this pass when its first two digits match the internal state/territory FIPS crosswalk and its county suffix is not `000`.
- Original `state_code` and `county_code` are preserved.
- Source flags document whether normalized values came from state code, county-code prefix fallback, county components, or missing/unmapped cases.

The post-2018 prefix fix was necessary because QA found rows where `county_fips_5` was present but `state_fips_2` was null, and rows where the `county_fips_5` prefix did not match `state_fips_2`. After cleanup:

- Prefix mismatches after cleanup: 0.
- Null-state aggregate rows after cleanup: 0.
- County-year aggregate rows after cleanup: 58,006.
- Rows excluded from county-level aggregates due to missing geography: 6,953,426.

Missing `county_fips_5` by year:

| year | missing county_fips_5 |
| ---: | ---: |
| 2007 | 795,010 |
| 2008 | 641,620 |
| 2009 | 589,220 |
| 2010 | 371,488 |
| 2011 | 327,118 |
| 2012 | 352,923 |
| 2013 | 348,777 |
| 2014 | 320,233 |
| 2015 | 298,520 |
| 2016 | 277,748 |
| 2017 | 245,597 |
| 2018 | 359,902 |
| 2019 | 345,402 |
| 2020 | 301,904 |
| 2021 | 298,805 |
| 2022 | 445,296 |
| 2023 | 337,673 |
| 2024 | 296,190 |

Rows with missing county geography are excluded from the main county-year and lender-county-year tables and preserved in QA tables. This is transparent, but the missingness may not be random and should be considered in research design.

## 9. Action_Taken Mapping

The aggregation logic uses the following action-code mapping:

- Originated loans: `action_taken = '1'`.
- Denied applications: `action_taken = '3'`.
- Preapproval denials: `action_taken = '7'`, documented as preapproval denied but not included in `denied_applications`.

The `action_taken_metadata` table has 16 rows: eight action codes for `pre_2018` and eight for `post_2018`. Codes `1` and `3` are treated consistently across the two source eras for the current aggregate definitions.

This mapping matters because action-code definitions determine which records are counted as applications, originations, and denials. Preapproval outcomes are not the same as standard application denials, so code `7` is documented separately rather than folded into `denied_applications`. Remaining caveats are that HMDA action-code interpretation and reporting context may vary across time and should be checked before using denial rates as causal outcomes.

## 10. Lender Identifier Construction

The canonical lender identifier is `lender_id`, stored as text. It is constructed as:

- Pre-2018: `respondent_id`.
- Post-2018: `lei`.

The companion field `lender_id_type` records which identifier system is used. Storing lender IDs as strings preserves leading zeros and supports LEI values.

Missing `lender_id` counts by year in `loan_years_geo`:

| year | missing lender_id |
| ---: | ---: |
| 2007 | 0 |
| 2008 | 0 |
| 2009 | 0 |
| 2010 | 0 |
| 2011 | 0 |
| 2012 | 0 |
| 2013 | 0 |
| 2014 | 0 |
| 2015 | 0 |
| 2016 | 0 |
| 2017 | 0 |
| 2018 | 1,961 |
| 2019 | 21 |
| 2020 | 0 |
| 2021 | 0 |
| 2022 | 0 |
| 2023 | 0 |
| 2024 | 0 |

The lender-county-year main table has no rows excluded solely for missing lender IDs after requiring usable county geography. The missing lender IDs in 2018 and 2019 are in the missing-geography exclusion bucket.

The main limitation is cross-era continuity. A `respondent_id` before 2018 and an LEI after 2018 are not directly equivalent. The current `lender_id` is useful for within-era aggregation and table construction, but cross-era lender identity tracking requires an external crosswalk or institution metadata.

## 11. Fintech Classification Limitation

This project does not create a fintech lender classification.

The reason is explicit: no lender-name fields are available in the constructed canonical data. The research-readiness audit found:

- Explicit lender-name columns in `loan_years_geo`: none.
- Lender-name keys retained in `raw_source_columns`: none.
- Available lender identifier/name-like columns in `loan_years_geo`: `lender_id`, `lender_id_type`.
- Available lender identifier/name-like keys retained in `raw_source_columns`: `lei`, `respondent_id`.

Because lender names are absent, keyword-based fintech classification was intentionally not run. Running a fintech keyword classifier without lender names would not be credible.

The correct next step is external lender enrichment using available lender IDs, LEIs, respondent IDs, HMDA institution metadata, or another verified lender identity source. Only after this enrichment should fintech shares be computed.

Proposed future tables:

| future table | purpose |
| --- | --- |
| `lender_identity_crosswalk` | Map respondent IDs, LEIs, institution names, and years across the 2018 schema break. |
| `lender_classification` | Store externally validated lender classifications, including fintech/nonbank flags and classification provenance. |
| `county_year_fintech_lending` | County-year aggregates with fintech shares and fintech volumes, built only after validated lender classification. |

## 12. Econometric Readiness And Limitations

The dataset is ready for:

- Descriptive county-year lending trends.
- Application, origination, and denial volumes over time.
- County-level lending intensity analysis after adding denominators.
- Lender presence and concentration measures.
- Lender-county-year panel construction.
- Pre/post descriptive analysis around 2018, with schema caveats.

The dataset is not yet ready for:

- Causal claims about fintech expansion.
- Definitive fintech share estimation.
- Cross-era lender identity tracking without enrichment.
- County-level demand normalization without population, income, housing, unemployment, mortgage market size, or credit-market controls.

Econometric design principles for future work:

- The panel grain must match the research question. County-year outcomes, lender-county-year outcomes, and lender-year outcomes answer different questions.
- Outcome definitions must be stable across years. The 2018 schema break requires caution.
- Missing geography exclusions may not be random and should be evaluated.
- Lender classification must be externally validated before computing fintech treatment or exposure measures.
- Causal analysis would require controls, fixed effects, and identification assumptions beyond this data build.

## 13. Data Quality Checks Performed

Completed QA included:

- Raw download manifest inspection.
- Parquet conversion metadata inspection.
- Row count reconciliation between conversion metadata and database views.
- Database QA of `loan_years` and `year_summary`.
- Geography normalization QA.
- County-year aggregate QA.
- Research-readiness audit.
- Lender-county-year checks.
- Export validation, including DuckDB readback of the lender-county-year Parquet file.

Headline QA numbers:

| check | result |
| --- | ---: |
| Loan-level rows processed | 312,095,276 |
| Years covered | 18 |
| Year range | 2007-2024 |
| Conversion metadata records | 18 |
| Conversion metadata error count | 0 |
| Included applications in `county_year_lending` | 305,141,850 |
| Excluded missing-geography rows | 6,953,426 |
| `county_year_lending` rows | 58,006 |
| `lender_county_year` rows | 8,923,506 |
| County-year null aggregate keys | 0 |
| County-year duplicate grain rows | 0 |
| Prefix mismatches after geography cleanup | 0 |
| Null-state aggregate rows after geography cleanup | 0 |
| Lender-county-year duplicate grain rows | 0 |
| Lender-county-year null main-table keys | 0 |

Export validation confirmed that `output/lender_county_year.parquet` can be read by DuckDB and contains 8,923,506 rows, years 2007-2024, 18 distinct years, and 24 columns.

## 14. Final Exported Outputs

| file | format | rows | size bytes | intended use | format rationale |
| --- | --- | ---: | ---: | --- | --- |
| `output/county_year_lending.csv` | CSV | 58,006 | 3,975,752 | County-year analysis and easy inspection. | Small enough for CSV. |
| `output/lender_county_year.parquet` | Parquet | 8,923,506 | 129,077,088 | Lender-county-year analysis and large-table workflows. | Large table; Parquet preserves types and is more efficient for analytics. |
| `output/lender_county_year_sample.csv` | CSV | 100,000 | 10,369,968 | Spreadsheet-friendly inspection sample. | Sample CSV avoids exporting the full large table as raw CSV. |
| `output/export_manifest.csv` | CSV | 3 | 725 | Export audit trail. | Small manifest table. |

The full lender-county-year table is exported as Parquet because it has millions of rows and should remain columnar. A full compressed CSV can be created later with `python -m scripts.export_tables --include-large-csv`, but it was not created in the default export run.

Only the small CSV exports and export manifest are committed to GitHub. The full `output/lender_county_year.parquet` export is generated locally by `python -m scripts.export_tables` and is excluded from GitHub by `.gitignore`.

## 15. Reproducibility

The project scripts support the following reproduction sequence.

Lightweight URL validation:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-via-HMDA_USER_AGENT)"
python -m scripts.download --validate-urls --years 2007 2018
```

Raw download:

```powershell
$env:HMDA_USER_AGENT = "hmda-county-panel-research/0.1 (contact: set-via-HMDA_USER_AGENT)"
python -m scripts.download --download --all-years --timeout-seconds 300 --retries 5 --backoff-seconds 10 --min-free-gb 100 --manifest data\raw\download_manifest.json
```

Convert annual raw files to Parquet:

```powershell
python -m scripts.convert --all-years
```

Build DuckDB:

```powershell
python -m scripts.build_db --all-years --force
```

Normalize geography:

```powershell
python -m scripts.normalize_geography
```

Build county-year aggregate:

```powershell
python -m scripts.build_county_year_lending
```

Run research-readiness audit:

```powershell
python -m scripts.research_readiness_audit
```

Build lender-county-year aggregate:

```powershell
python -m scripts.build_lender_county_year
```

Export default outputs:

```powershell
python -m scripts.export_tables
```

Optional full compressed lender-county-year CSV:

```powershell
python -m scripts.export_tables --include-large-csv
```

## 16. Recommended Next Steps

### A. Add Lender Identity Enrichment

- Obtain lender names or institution metadata.
- Map pre-2018 respondent IDs and post-2018 LEIs across the schema break.
- Create a verified lender classification table with explicit provenance.

### B. Build Fintech And Nonbank Measures

- County-year fintech shares.
- Lender entry and exit by county.
- First year of lender presence by county.
- Expansion margins by lender and county.

### C. Add County Controls

- Population.
- Income.
- Housing stock.
- Unemployment.
- Mortgage market size.

### D. Prepare Econometric Specifications

- County fixed effects.
- Year fixed effects.
- Lender fixed effects where appropriate.
- Event-study or difference-in-differences designs only after a defensible treatment definition exists.

## 17. Caveats

- HMDA has a major schema break in 2018.
- Lender identifiers are discontinuous across `respondent_id` and LEI without additional crosswalks.
- Missing geography rows are excluded from county-level and lender-county-level main aggregates.
- The canonical data contains lender IDs but no lender names.
- Raw HMDA variable definitions and reporting context may change over time.
- Aggregate counts depend on the chosen `action_taken` mapping.
- The output is a data foundation, not a final causal analysis.

## 18. Short Conclusion

The project successfully created a reproducible large-scale HMDA panel foundation for 2007-2024. The county-year and lender-county-year outputs are ready for descriptive and preparatory analysis of mortgage-lending geography and lender presence. The main remaining blocker for the original fintech-expansion question is lender identity and classification enrichment.
