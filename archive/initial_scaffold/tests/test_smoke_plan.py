import unittest

from hmda_plan.config import ConfigError, parse_smoke_test_config
from hmda_plan.smoke_test import build_plan


VALID_CONFIG = {
    "years": [2022, 2023],
    "input_mode": "manifest_only",
    "max_rows_per_year": 1000,
    "required_columns": ["activity_year", "lei"],
    "checks": ["config_valid", "no_network_required"],
}


class SmokePlanTests(unittest.TestCase):
    def test_parse_valid_two_year_config(self) -> None:
        config = parse_smoke_test_config(VALID_CONFIG)

        self.assertEqual(config.years, (2022, 2023))
        self.assertEqual(config.input_mode, "manifest_only")
        self.assertEqual(config.max_rows_per_year, 1000)
        self.assertEqual(config.required_columns, ("activity_year", "lei"))

    def test_rejects_more_than_two_years(self) -> None:
        raw = {**VALID_CONFIG, "years": [2021, 2022, 2023]}

        with self.assertRaises(ConfigError):
            parse_smoke_test_config(raw)

    def test_rejects_non_manifest_mode_initially(self) -> None:
        raw = {**VALID_CONFIG, "input_mode": "local_files"}

        with self.assertRaises(ConfigError):
            parse_smoke_test_config(raw)

    def test_build_plan_is_dry_run_only(self) -> None:
        config = parse_smoke_test_config(VALID_CONFIG)

        plan = "\n".join(build_plan(config))

        self.assertIn("No network requests will be made.", plan)
        self.assertIn("No full-scale processing will be run.", plan)


if __name__ == "__main__":
    unittest.main()
