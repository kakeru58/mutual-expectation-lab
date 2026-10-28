"""Reproduce the published pointwise intervals and paired condition contrasts."""

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from expectation_lab.scheduling import keyed
from expectation_lab.storage import write_csv, write_json


def communication_patterns(index, pairs, seeds, checkpoints):
    records = []
    for pair in pairs:
        for condition in ("P_P", "E_P", "E_E"):
            paths = [
                [
                    float(index[pair, seed, condition, cp]["request_count"])
                    + float(index[pair, seed, condition, cp]["cancel_count"])
                    for cp in checkpoints
                ]
                for seed in seeds
            ]
            records.append(
                {
                    "pair_id": pair,
                    "condition": condition,
                    "n_seeds": len(seeds),
                    "ever_communicates": sum(max(path) > 0 for path in paths),
                    "no_communication_at_any_checkpoint": sum(
                        max(path) == 0 for path in paths
                    ),
                    "communication_disappears_by_last_checkpoint": sum(
                        path[-1] == 0 and max(path[:-1], default=0) > 0
                        for path in paths
                    ),
                    "communication_present_at_last_checkpoint": sum(
                        path[-1] > 0 for path in paths
                    ),
                    "communication_decreases_from_20_to_50": (
                        sum(path[checkpoints.index(20)] > path[-1] for path in paths)
                        if 20 in checkpoints
                        else ""
                    ),
                    "communication_increases_from_20_to_50": (
                        sum(path[checkpoints.index(20)] < path[-1] for path in paths)
                        if 20 in checkpoints
                        else ""
                    ),
                }
            )
    return records


def summarize(run, output, design):
    """Pointwise paired seed bootstrap; shared indices across pairs/stages/conditions."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (Path(run) / "curves.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    seeds = design["seeds"]
    pairs = design["pairs"]
    cps = design["checkpoints"]
    config = design["config"]
    index = {
        (int(r["pair_id"]), int(r["seed"]), r["condition"], int(r["checkpoint"])): r
        for r in rows
    }
    write_csv(
        output / "communication_patterns.csv",
        communication_patterns(index, pairs, seeds, cps),
    )
    rng = keyed(
        config["statistics"]["bootstrap_seed"], "learning_curve_paired_bootstrap"
    )
    reps = config["statistics"]["bootstrap_replicates"]
    samples = [[rng.randrange(len(seeds)) for _ in seeds] for _ in range(reps)]
    metrics = [
        "joint_success",
        "joint_task_cost",
        "communication_count",
        "communication_episode_rate",
        "log_loss",
    ]

    def number(row, metric):
        return (
            float(row["request_count"]) + float(row["cancel_count"])
            if metric == "communication_count"
            else float(row[metric])
        )

    def interval(values):
        draws = sorted(
            sum(values[i] for i in sample) / len(values) for sample in samples
        )

        def quantile(p):
            pos = (len(draws) - 1) * p
            low = int(pos)
            high = min(low + 1, len(draws) - 1)
            return draws[low] + (draws[high] - draws[low]) * (pos - low)

        return mean(values), quantile(0.025), quantile(0.975)

    summaries = []
    contrasts = []
    for scope in pairs + ["all"]:
        selected = pairs if scope == "all" else [scope]
        for cp in cps:
            for metric in metrics:
                for condition in config["conditions"]:
                    cid = condition["id"]
                    values = [
                        mean(number(index[p, s, cid, cp], metric) for p in selected)
                        for s in seeds
                    ]
                    avg, low, high = interval(values)
                    summaries.append(
                        {
                            "pair_id": scope,
                            "condition": cid,
                            "checkpoint": cp,
                            "metric": metric,
                            "mean": avg,
                            "low95": low,
                            "high95": high,
                            "n_seeds": len(seeds),
                            "bootstrap_replicates": reps,
                        }
                    )
                for hi, lo in config["statistics"]["contrasts"]:
                    values = [
                        mean(
                            number(index[p, s, hi, cp], metric)
                            - number(index[p, s, lo, cp], metric)
                            for p in selected
                        )
                        for s in seeds
                    ]
                    avg, low, high = interval(values)
                    contrasts.append(
                        {
                            "pair_id": scope,
                            "contrast": hi + "-" + lo,
                            "checkpoint": cp,
                            "metric": metric,
                            "difference": avg,
                            "low95": low,
                            "high95": high,
                            "n_seeds": len(seeds),
                            "bootstrap_replicates": reps,
                        }
                    )
    write_csv(output / "curve_intervals.csv", summaries)
    write_csv(output / "paired_contrasts.csv", contrasts)
    write_json(
        output / "bootstrap_protocol.json",
        {
            "replicates": reps,
            "seed": config["statistics"]["bootstrap_seed"],
            "unit": "simulation_seed",
            "shared_resampling_indices": True,
            "equal_pair_weight": True,
            "interval_type": "pointwise_percentile_95",
            "multiple_comparison_adjustment": False,
            "population_interpretation": "simulation_seed_variation_only",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/full"))
    args = parser.parse_args()
    design = json.loads((args.run / "design.json").read_text())
    summarize(args.run, args.run / "paper_stats", design)
    print(args.run / "paper_stats")
