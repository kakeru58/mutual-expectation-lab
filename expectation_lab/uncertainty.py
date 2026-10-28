"""Paired bootstrap over simulation seeds, with shared indices for every comparison."""

from statistics import mean
from .simulation import keyed
from .storage import write_csv


def bootstrap(curves, config, seeds, pairs, checkpoints, output):
    if len(seeds) < 2:
        return  # A single seed does not estimate seed-to-seed variation.
    index = {
        (r["pair_id"], r["seed"], r["condition"], r["checkpoint"]): r for r in curves
    }
    rng = keyed(
        config["statistics"]["bootstrap_seed"], "learning_curve_paired_bootstrap"
    )
    samples = [
        [rng.randrange(len(seeds)) for _ in seeds]
        for _ in range(config["statistics"]["bootstrap_replicates"])
    ]

    def interval(values):
        draws = sorted(
            sum(values[i] for i in sample) / len(values) for sample in samples
        )

        def quantile(p):
            position = (len(draws) - 1) * p
            lo = int(position)
            hi = min(lo + 1, len(draws) - 1)
            return draws[lo] + (draws[hi] - draws[lo]) * (position - lo)

        return mean(values), quantile(0.025), quantile(0.975)

    result = []
    for scope in pairs + ["all"]:
        selected = pairs if scope == "all" else [scope]
        for cp in checkpoints:
            for metric in (
                "joint_success",
                "joint_task_cost",
                "communications_per_episode",
            ):
                for hi, lo in config["statistics"]["contrasts"]:
                    values = [
                        mean(
                            index[p, s, hi, cp][metric] - index[p, s, lo, cp][metric]
                            for p in selected
                        )
                        for s in seeds
                    ]
                    avg, low, high = interval(values)
                    result.append(
                        {
                            "pair_id": scope,
                            "checkpoint": cp,
                            "contrast": hi + "-" + lo,
                            "metric": metric,
                            "difference": avg,
                            "low95": low,
                            "high95": high,
                            "n_seeds": len(seeds),
                        }
                    )
    write_csv(output / "paired_contrasts.csv", result)
