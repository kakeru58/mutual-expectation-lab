"""Stream each raw log once, verify stored summaries, then summarize 12 scenes."""

from collections import defaultdict
import csv
from pathlib import Path
from statistics import mean
from .metrics import summarize_episode
from .storage import read_steps, write_csv, write_json


def episode_rows(path, config):
    group = []
    for row in read_steps(path):
        if group and row["episode_id"] != group[0]["episode_id"]:
            yield reduce(group, config)
            group = []
        group.append(row)
    if group:
        yield reduce(group, config)


def reduce(group, config):
    first = group[0]
    return {
        **summarize_episode(group, config),
        "checkpoint": first["checkpoint"],
        "block": first["block"],
    }


def curve(rows):
    result = {k: rows[0][k] for k in ("pair_id", "seed", "condition", "checkpoint")}
    requests = sum(r["request_A"] + r["request_B"] for r in rows)
    cancels = sum(r["cancel_A"] + r["cancel_B"] for r in rows)
    n = sum(r["prediction_n_A"] + r["prediction_n_B"] for r in rows)
    result.update(
        eval_episodes=len(rows),
        request_count=requests,
        cancel_count=cancels,
        communications_per_episode=(requests + cancels) / len(rows),
        communication_episode_rate=mean(
            int(r["request_A"] + r["request_B"] + r["cancel_A"] + r["cancel_B"] > 0)
            for r in rows
        ),
        prediction_n=n,
    )
    for metric in (
        "joint_success",
        "joint_task_cost",
        "settlement_time",
        "burden_difference",
        "timeout",
    ):
        result["timeout_rate" if metric == "timeout" else metric] = mean(
            r[metric] for r in rows
        )
    for metric in ("log_loss", "brier"):
        result[metric] = (
            sum(r[metric + "_sum_A"] + r[metric + "_sum_B"] for r in rows) / n
            if n
            else None
        )
    return result


def aggregate(output, config, expected_runs):
    output = Path(output)
    markers = sorted(output.glob("*/complete.json"))
    if len(markers) != expected_runs:
        raise ValueError(f"Incomplete design: {len(markers)}/{expected_runs} runs")
    curves, evaluation, train_blocks = [], [], []
    count = 0
    for marker in markers:
        directory = marker.parent
        rows = list(episode_rows(directory / "steps.jsonl.gz", config))
        with (directory / "episodes.csv").open() as stream:
            saved = list(csv.DictReader(stream))
        normalized = [
            {k: "" if v is None else str(v) for k, v in r.items()} for r in rows
        ]
        if normalized != saved:
            raise AssertionError(f"Raw log differs from saved CSV: {directory}")
        grouped = defaultdict(list)
        for row in rows:
            grouped[
                row["phase"],
                row["checkpoint"] if row["phase"] == "eval" else row["block"],
            ].append(row)
        for (phase, stage), group in grouped.items():
            if phase == "eval":
                curves.append(curve(group))
                evaluation.extend(group)
            else:
                train_blocks.append(
                    {
                        **{k: group[0][k] for k in ("pair_id", "seed", "condition")},
                        "completed_blocks": stage + 1,
                        "request_count": sum(
                            r["request_A"] + r["request_B"] for r in group
                        ),
                        "cancel_count": sum(
                            r["cancel_A"] + r["cancel_B"] for r in group
                        ),
                        "joint_task_cost": mean(r["joint_task_cost"] for r in group),
                    }
                )
        count += len(rows)
    write_csv(output / "curves.csv", curves)
    write_csv(output / "eval_by_context.csv", evaluation)
    write_csv(output / "training_by_block.csv", train_blocks)
    verified = {
        "runs": len(markers),
        "episodes": count,
        "eval_episodes": len(evaluation),
        "log_reaggregation_matches": True,
    }
    write_json(output / "verification.json", verified)
    return curves
