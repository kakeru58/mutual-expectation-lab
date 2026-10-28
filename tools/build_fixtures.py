"""Generate portable browser parity cases from a reference implementation."""

import argparse
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from expectation_lab.simulation import keyed, agents_for, episode, schedule

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=root / "tests/browser-fixtures.json")
args = parser.parse_args()
config = json.loads((root / "expectation_lab/config.json").read_text(encoding="utf-8"))
random_cases = []
for seed in range(20):
    key = (3, seed, 0, "context_order")
    rng = keyed(*key)
    order = list(range(12))
    rng.shuffle(order)
    key2 = (3, seed, 0, 0, 0, "A", "explore")
    random_cases.append(
        {
            "key": key,
            "shuffle": order,
            "draw_key": key2,
            "draw": keyed(*key2).random(),
            "choice": keyed(*key2).choice(["YIELD", "WAIT", "REQUEST"]),
        }
    )
cases = []
for pair in config["pairs"]:
    for condition in config["conditions"]:
        agents = agents_for(config, pair, condition)
        case = {"pair": pair["id"], "condition": condition["id"], "stages": {}}

        def evaluate(stage):
            outputs = []
            for cid in range(12):
                meta = dict(
                    run_id="parity",
                    pair_id=pair["id"],
                    condition=condition["id"],
                    seed=0,
                    phase="eval",
                    episode_id=cid,
                )
                logs = episode(config, agents, meta, cid)
                outputs.append(
                    [
                        {
                            "actor": r["actor"],
                            "selected": r["selected"],
                            "executed": r["executed"],
                            "state_after": r["state_after"],
                            "candidates": r["candidates"],
                            "q": r["q"],
                            "task_increment": r["task_increment"],
                            "expectation_increment": r["expectation_increment"],
                        }
                        for r in logs
                    ]
                )
            case["stages"][str(stage)] = outputs

        evaluate(0)
        for block, slot, cid in schedule(config, pair["id"], 0, 2):
            meta = dict(
                run_id="parity",
                pair_id=pair["id"],
                condition=condition["id"],
                seed=0,
                phase="train",
                episode_id=block * 12 + slot,
                block=block,
                slot=slot,
            )
            episode(config, agents, meta, cid, training=True)
        evaluate(2)
        case["observations_after_2"] = {
            i: agents[i].predictor.version for i in ("A", "B")
        }
        cases.append(case)
args.output.write_text(
    json.dumps({"random": random_cases, "cases": cases}, ensure_ascii=False)
)
print("Generated 20 RNG cases and 360 frozen episodes from the Python model.")
