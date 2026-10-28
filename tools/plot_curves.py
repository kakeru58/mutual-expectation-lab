"""Plot the published learning curves from a reproduced run. Requires Matplotlib."""

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import mean

COLORS = {"P_P": "#78838b", "E_P": "#3f72b7", "E_E": "#147d68"}
TITLES = {
    1: "Pair 1: selective demands",
    2: "Pair 2: asymmetric demand criteria",
    3: "Pair 3: symmetric demands",
    4: "Pair 4: asymmetric yielding costs",
    5: "Pair 5: broad and strong A demand",
}


def read_curves(output):
    rows = list(csv.DictReader((output / "curves.csv").open()))
    grouped = defaultdict(list)
    for r in rows:
        grouped[int(r["pair_id"]), r["condition"], int(r["checkpoint"])].append(r)
    averaged = []
    for (pair, condition, cp), group in sorted(grouped.items()):
        averaged.append(
            {
                "pair_id": pair,
                "condition": condition,
                "checkpoint": cp,
                **{
                    k: mean(float(r[k]) for r in group)
                    for k in (
                        "joint_success",
                        "joint_task_cost",
                        "request_count",
                        "cancel_count",
                        "log_loss",
                        "brier",
                        "settlement_time",
                    )
                },
            }
        )
    return rows, averaged


def plot(output, averaged):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pairs = sorted({r["pair_id"] for r in averaged})
    cps = sorted({r["checkpoint"] for r in averaged})
    intervals = {}
    if (output / "paper_stats/curve_intervals.csv").exists():
        intervals = {
            (r["pair_id"], r["condition"], int(r["checkpoint"]), r["metric"]): r
            for r in csv.DictReader((output / "paper_stats/curve_intervals.csv").open())
        }
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axes = plt.subplots(
        len(pairs), 3, figsize=(12.8, 3.1 * len(pairs)), squeeze=False
    )
    for row, pair in enumerate(pairs):
        for col, metric in enumerate(("communication", "joint_task_cost", "log_loss")):
            ax = axes[row, col]
            for condition in ("P_P", "E_P", "E_E"):
                values = sorted(
                    (
                        r
                        for r in averaged
                        if r["pair_id"] == pair and r["condition"] == condition
                    ),
                    key=lambda r: r["checkpoint"],
                )
                y = [
                    (
                        r["request_count"] + r["cancel_count"]
                        if metric == "communication"
                        else r[metric]
                    )
                    for r in values
                ]
                x = [cps.index(r["checkpoint"]) for r in values]
                ax.plot(
                    x,
                    y,
                    marker="o",
                    markersize=4,
                    color=COLORS[condition],
                    linewidth=1.8,
                    label=condition,
                )
                m = "communication_count" if metric == "communication" else metric
                ci = [
                    intervals.get((str(pair), condition, r["checkpoint"], m))
                    for r in values
                ]
                if ci and all(ci):
                    ax.fill_between(
                        x,
                        [float(r["low95"]) for r in ci],
                        [float(r["high95"]) for r in ci],
                        color=COLORS[condition],
                        alpha=0.12,
                        linewidth=0,
                    )
            ax.set_xticks(range(len(cps)), [str(c) for c in cps])
            ax.set_xlabel("Completed training blocks")
            ax.grid(axis="y", alpha=0.18)
            ax.set_axisbelow(True)
            ax.set_title(TITLES.get(pair, f"Pair {pair}"), loc="left", fontsize=10)
            ax.set_ylabel(
                {
                    "communication": "REQUEST + CANCEL / 12 eval episodes",
                    "joint_task_cost": "Mean joint task cost",
                    "log_loss": "Observed-action log loss",
                }[metric]
            )
            if metric == "communication":
                ax.set_ylim(bottom=-0.15)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1),
    )
    fig.suptitle(
        "Frozen-policy evaluations along continuous mutual learning",
        y=1.035,
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0.025, 1, 0.96))
    fig.text(
        0.02,
        0.005,
        "Equally spaced checkpoints. Shading, when present: pointwise 95% seed bootstrap. Evaluation: no exploration/updates; observed-action distributions vary.",
        fontsize=8,
        color="#5e6871",
    )
    for extension in ("png", "svg", "pdf"):
        fig.savefig(
            output / f"learning_curves.{extension}", dpi=170, bbox_inches="tight"
        )
    plt.close(fig)
    import importlib.metadata

    write = {
        d.metadata["Name"]: d.version
        for d in importlib.metadata.distributions()
        if d.metadata.get("Name", "").lower()
        in (
            "matplotlib",
            "numpy",
            "pillow",
            "contourpy",
            "cycler",
            "fonttools",
            "kiwisolver",
            "packaging",
            "pyparsing",
            "python-dateutil",
            "six",
            "tzdata",
        )
    }
    (output / "plot_versions.json").write_text(json.dumps(write, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=Path("runs/full"))
    args = parser.parse_args()
    _, curves = read_curves(args.run)
    plot(args.run, curves)
    print(args.run / "learning_curves.png")
