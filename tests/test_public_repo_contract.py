import unittest
from pathlib import Path

from scripts.build_county_year_lending import COUNTY_YEAR_SQL
from scripts.build_lender_county_year import LENDER_COUNTY_YEAR_SQL
from scripts.export_tables import LENDER_SAMPLE_CSV_PATH, planned_exports


class PublicRepoContractTests(unittest.TestCase):
    def test_readme_points_to_active_test_suite(self) -> None:
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("python -m unittest discover -s tests", readme)
        self.assertTrue(Path("tests/test_convert.py").exists())
        self.assertTrue(Path("tests/test_public_repo_contract.py").exists())

    def test_county_aggregate_splits_record_denominators(self) -> None:
        self.assertIn("COUNT(*) AS total_records", COUNTY_YEAR_SQL)
        self.assertIn("AS application_records", COUNTY_YEAR_SQL)
        self.assertIn("AS purchased_loans", COUNTY_YEAR_SQL)
        self.assertIn("COUNT(*) AS total_applications", COUNTY_YEAR_SQL)

    def test_lender_aggregate_splits_record_denominators(self) -> None:
        self.assertIn("COUNT(*) AS records", LENDER_COUNTY_YEAR_SQL)
        self.assertIn("AS application_records", LENDER_COUNTY_YEAR_SQL)
        self.assertIn("AS purchased_loans", LENDER_COUNTY_YEAR_SQL)
        self.assertIn("COUNT(*) AS applications", LENDER_COUNTY_YEAR_SQL)

    def test_lender_sample_is_stratified_by_year(self) -> None:
        exports = planned_exports(include_large_csv=False)
        sample_exports = [export for export in exports if export[2] == LENDER_SAMPLE_CSV_PATH]

        self.assertEqual(len(sample_exports), 1)
        sample_query = sample_exports[0][3]
        self.assertIn("PARTITION BY activity_year", sample_query)
        self.assertIn("sample_rows_per_year", sample_query)
        self.assertIn("state_name", sample_query)


if __name__ == "__main__":
    unittest.main()
