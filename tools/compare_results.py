"""Compare a complete learning-curve run with the published reference CSV."""

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("pair_id", "seed", "condition", "checkpoint")


def read(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def compare(reference, actual):
    key = lambda row: tuple(row[name] for name in KEYS)
    expected = {key(row): row for row in reference}
    observed = {key(row): row for row in actual}
    if len(expected) != len(reference) or len(observed) != len(actual):
        raise ValueError("Duplicate evaluation keys")
    if expected.keys() != observed.keys():
        raise ValueError("The run does not cover the published design")
    for case, row in expected.items():
        if row != observed[case]:
            raise ValueError(f"Result differs at {case}")
    print(f"PASS: all {len(expected)} evaluation summaries match the reference.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/full"))
    args = parser.parse_args()
    compare(read(ROOT / "docs/data/curves.csv"), read(args.run / "curves.csv"))
