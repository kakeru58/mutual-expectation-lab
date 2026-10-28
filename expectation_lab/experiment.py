"""A single repeated-partner run, with isolated checkpoint evaluations."""

import gzip
import json
import os
from pathlib import Path
import time
from .simulation import agents_for, contexts, episode, schedule
from .metrics import summarize_episode
from .storage import write_csv, write_json


def run_one(config, pair, condition, seed, checkpoints, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / "complete.json"
    if marker.exists():
        return "skipped"
    started = time.perf_counter()
    agents = agents_for(config, pair, condition)
    base = {
        "run_id": f"p{pair['id']}_{condition['id']}_s{seed}",
        "pair_id": pair["id"],
        "condition": condition["id"],
        "seed": seed,
    }
    summaries = []
    temporary = directory / "steps.jsonl.gz.partial"
    n_contexts = len(contexts(config))
    with gzip.open(temporary, "wt", encoding="utf-8", compresslevel=1) as stream:

        def save(logs, checkpoint):
            for row in logs:
                stream.write(
                    json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                )
            summaries.append(
                {
                    **summarize_episode(logs, config),
                    "checkpoint": checkpoint,
                    "block": logs[0].get("block", -1),
                }
            )

        def evaluate(blocks):
            before = {i: agents[i].predictor.export() for i in ("A", "B")}
            write_json(directory / f"predictors_b{blocks:02}.json", before)
            frozen = agents_for(
                config, pair, condition, {i: agents[i].predictor for i in ("A", "B")}
            )
            for cid in range(n_contexts):
                meta = {
                    **base,
                    "phase": "eval",
                    "episode_id": f"eval_b{blocks}_c{cid}",
                    "checkpoint": blocks,
                    "block": -1,
                    "slot": cid,
                }
                save(episode(config, frozen, meta, cid), blocks)
            assert before == {i: frozen[i].predictor.export() for i in ("A", "B")}
            assert before == {i: agents[i].predictor.export() for i in ("A", "B")}

        if 0 in checkpoints:
            evaluate(0)
        for block, slot, cid in schedule(config, pair["id"], seed, max(checkpoints)):
            meta = {
                **base,
                "phase": "train",
                "episode_id": block * n_contexts + slot,
                "checkpoint": None,
                "block": block,
                "slot": slot,
            }
            save(episode(config, agents, meta, cid, training=True), None)
            if slot == n_contexts - 1 and block + 1 in checkpoints:
                evaluate(block + 1)
    os.replace(temporary, directory / "steps.jsonl.gz")
    write_csv(directory / "episodes.csv", summaries)
    write_json(
        marker,
        {
            **base,
            "episodes": len(summaries),
            "frozen_checks": len(checkpoints),
            "elapsed_seconds": time.perf_counter() - started,
        },
    )
    return "completed"
