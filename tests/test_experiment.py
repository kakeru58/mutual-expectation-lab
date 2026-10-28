import csv
import json
from pathlib import Path
import tempfile
import unittest
from helpers import CONFIG
from expectation_lab.aggregate import aggregate
from expectation_lab.experiment import run_one
from expectation_lab.storage import read_steps


class ExperimentTests(unittest.TestCase):
    def test_T23_log_reaggregation_and_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "p1_P_P_s0"
            args = (
                CONFIG,
                CONFIG["pairs"][0],
                CONFIG["conditions"][0],
                0,
                [0, 2],
                directory,
            )
            self.assertEqual(run_one(*args), "completed")
            rows = aggregate(root, CONFIG, 1)
            self.assertEqual(len(rows), 2)
            self.assertEqual(
                json.loads((root / "verification.json").read_text())["episodes"], 48
            )
            marker = directory / "complete.json"
            stamp = marker.stat().st_mtime_ns
            self.assertEqual(run_one(*args), "skipped")
            self.assertEqual(stamp, marker.stat().st_mtime_ns)
            path = directory / "episodes.csv"
            original = path.read_text()
            path.write_text(original.replace(",13,", ",999,", 1))
            # Corrupt a known field independently of the raw log.
            with path.open() as stream:
                saved = list(csv.DictReader(stream))
            saved[0]["joint_task_cost"] = "999"
            from expectation_lab.storage import write_csv

            write_csv(path, saved)
            with self.assertRaises(AssertionError):
                aggregate(root, CONFIG, 1)

    def test_checkpoint_evaluation_does_not_change_training(self):
        with tempfile.TemporaryDirectory() as temporary:
            a, b = Path(temporary) / "a", Path(temporary) / "b"
            common = (CONFIG, CONFIG["pairs"][2], CONFIG["conditions"][2], 0)
            run_one(*common, [0, 2], a)
            run_one(*common, [2], b)
            self.assertEqual(
                (a / "predictors_b02.json").read_text(),
                (b / "predictors_b02.json").read_text(),
            )

            def training(path):
                rows = [
                    r
                    for r in read_steps(path / "steps.jsonl.gz")
                    if r["phase"] == "train"
                ]
                for r in rows:
                    r.pop("planning_seconds")
                return rows

            self.assertEqual(training(a), training(b))
            self.assertEqual(
                sum(
                    p["version"]
                    for p in json.loads(
                        (a / "predictors_b00.json").read_text()
                    ).values()
                ),
                0,
            )
