# Export Outputs

## Scope

This export step creates researcher-facing files from existing DuckDB tables. It does not download data, delete raw or Parquet files, classify fintech lenders, or rebuild the database.

The small CSV outputs and manifest are committed for public review. The full lender-county-year Parquet export is generated locally and is not committed to GitHub.

## Source Row Counts

| table | row_count |
| --- | --- |
| county_year_lending | 58,006 |
| lender_county_year | 8,923,506 |

## Exported Files

| file | table | format | rows | size_bytes | status |
| --- | --- | --- | --- | --- | --- |
| county_year_lending.csv | county_year_lending | csv | 58,006 | 3,975,752 | exported |
| lender_county_year.parquet | lender_county_year | parquet | 8,923,506 | 129,077,088 | exported |
| lender_county_year_sample.csv | lender_county_year | csv | 100,000 | 10,369,968 | exported |

## Large Table Format

`lender_county_year` is exported as Parquet by default because it has millions of rows. Parquet is smaller, typed, faster to read with DuckDB, R, Python, and other analytics tools, and avoids the large disk footprint and slower parsing of a raw CSV.

A 100,000-row CSV sample is exported for quick inspection in spreadsheet tools.

In the public GitHub repository, regenerate the full Parquet export with:

```powershell
python -m scripts.export_tables
```

## Full CSV Option

To create a full compressed CSV later, run:

```powershell
python -m scripts.export_tables --include-large-csv
```

That optional command writes `output/lender_county_year.csv.gz` in addition to the default outputs.

Full compressed CSV included in this run: `False`
