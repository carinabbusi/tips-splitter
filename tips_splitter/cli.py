"""Command line usage: python -m tips_splitter.cli data/sample_tips.csv"""

from __future__ import annotations

import argparse
import sys

from .loader import load_entries
from .splitter import TipSplitError, split_period


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split tips equally among the team.")
    parser.add_argument("csv_file", help="CSV with columns date,amount,workers")
    args = parser.parse_args(argv)

    try:
        report = split_period(load_entries(args.csv_file))
    except (TipSplitError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Total collected: EUR {report.total}\n")
    print(f"{'Person':<15}{'Days':>6}{'To receive':>14}")
    for name, amount in report.per_person.items():
        print(f"{name:<15}{report.days_worked[name]:>6}{'EUR ' + str(amount):>14}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
