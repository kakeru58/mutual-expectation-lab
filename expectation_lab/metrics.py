"""Reduce raw episode increments into measured outcomes."""

from .environment import IDS


def summarize_episode(logs, config):
    first, last = logs[0], logs[-1]
    row = {
        k: first[k]
        for k in (
            "run_id",
            "pair_id",
            "condition",
            "seed",
            "phase",
            "episode_id",
            "context_id",
        )
    }
    final = last["state_after"]
    row["joint_success"] = int(final["p_A"] == final["p_B"] == "done")
    row["timeout"] = int(last["termination"] == "timeout")
    row["unresolved"] = int(final["first_yielder"] is None)
    row["first_yielder"] = final["first_yielder"] or ""
    row["settlement_time"] = next(
        (r["state_after"]["t"] for r in logs if r["settlement"] == "yield"),
        config["horizon"],
    )
    row["d_group"] = "".join(
        str(
            first["expectation"][i]["g"]
            * first["evaluation_only"]["counterfactual_d"][i]
        )
        for i in IDS
    )
    for i in IDS:
        row["arrived_" + i] = int(final["p_" + i] == "done")
        row["arrival_" + i] = next(
            (
                r["state_after"]["t"]
                for r in logs
                if r["actor"] == i and r["executed"] == "PASS"
            ),
            config["horizon"],
        )
        row["task_cost_" + i] = sum(r["task_increment"][i] for r in logs)
        row["expectation_cost_" + i] = sum(r["expectation_increment"][i] for r in logs)
        row["total_cost_" + i] = row["task_cost_" + i] + row["expectation_cost_" + i]
        for a in ("YIELD", "REQUEST", "CANCEL"):
            row[a.lower() + "_" + i] = sum(
                r["actor"] == i and r["executed"] == a for r in logs
            )
        settled = next((r for r in logs if r["L"][i] is not None), None)
        row["L_" + i] = settled["L"][i] if settled else ""
        eligible = bool(
            settled
            and settled["expectation"][i]["g"]
            and settled["evaluation_only"]["settlement_d"][i]
        )
        row["fulfillment_denominator_" + i] = int(eligible)
        row["fulfilled_" + i] = int(eligible and settled["L"][i] == 0)
        scores = [
            r["prediction_score"]
            for r in logs
            if r["q_observer"] == i and r["prediction_score"]["included"]
        ]
        row["prediction_n_" + i] = len(scores)
        row["prediction_excluded_" + i] = sum(
            r["q_observer"] == i and not r["prediction_score"]["included"] for r in logs
        )
        for score in ("log_loss", "brier"):
            row[score + "_sum_" + i] = sum(r[score] for r in scores)
    row["joint_task_cost"] = row["task_cost_A"] + row["task_cost_B"]
    row["burden_difference"] = abs(row["task_cost_A"] - row["task_cost_B"])
    return row
