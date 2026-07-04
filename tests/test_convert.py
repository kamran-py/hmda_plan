import unittest
from pathlib import Path

from scripts.convert import PreparedInput, output_columns, raw_alias, select_expressions


class ConvertSqlTests(unittest.TestCase):
    def test_raw_alias_preserves_canonical_activity_year(self) -> None:
        self.assertEqual(raw_alias("activity_year"), "raw_activity_year")
        self.assertEqual(raw_alias("county_code"), "county_code")

    def test_2007_selects_canonical_fields(self) -> None:
        prepared = PreparedInput(
            year=2007,
            source_era="pre_2018",
            raw_input_path=Path("data/raw/hmda_2007_nationwide.zip"),
            readable_csv_path=Path("data/raw/.convert_tmp/2007/file.csv"),
            parquet_output_path=Path("data/parquet/hmda_2007.parquet"),
            input_columns=["as_of_year", "respondent_id", "state_code", "county_code"],
        )

        expressions = select_expressions(prepared)

        self.assertIn('TRY_CAST("as_of_year" AS INTEGER) AS activity_year', expressions)
        self.assertIn("'pre_2018' AS source_era", expressions)
        self.assertIn('"respondent_id" AS lei_or_respondent_id', expressions)
        self.assertIn("activity_year", output_columns(prepared))

    def test_2018_raw_activity_year_is_kept_with_alias(self) -> None:
        prepared = PreparedInput(
            year=2018,
            source_era="post_2018",
            raw_input_path=Path("data/raw/hmda_2018_nationwide.csv"),
            readable_csv_path=Path("data/raw/hmda_2018_nationwide.csv"),
            parquet_output_path=Path("data/parquet/hmda_2018.parquet"),
            input_columns=["activity_year", "lei", "state_code", "county_code"],
        )

        self.assertIn("raw_activity_year", output_columns(prepared))
        self.assertIn('"activity_year" AS "raw_activity_year"', select_expressions(prepared))


if __name__ == "__main__":
    unittest.main()
