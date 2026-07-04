from __future__ import annotations

import argparse

from scripts.build_db import build_database_plan
from scripts.convert import build_conversion_plan
from scripts.download import build_download_plan
from scripts.config import SMOKE_TEST_YEARS


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the dry-run HMDA pipeline plan.")
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=list(SMOKE_TEST_YEARS),
        help="Years to include in the dry-run plan. Defaults to the 2007/2018 smoke test.",
    )
    args = parser.parse_args()

    sections = [
        ("DOWNLOAD", build_download_plan(args.years)),
        ("CONVERT", build_conversion_plan(args.years)),
        ("BUILD_DB", build_database_plan(args.years)),
    ]
    for title, lines in sections:
        print(f"[{title}]")
        for line in lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
