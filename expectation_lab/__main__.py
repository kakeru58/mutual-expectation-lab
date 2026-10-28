"""Run a smoke test, the original final evaluation, or the six-point learning curve."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
from .aggregate import aggregate
from .experiment import run_one
from .storage import source_hashes, write_json
from .uncertainty import bootstrap

ROOT = Path(__file__).resolve().parents[1]
PRESETS = {
    "smoke": ([1], [0], [2]),
    "main": (list(range(1, 6)), list(range(20)), [50]),
    "curves": (list(range(1, 6)), list(range(20)), [0, 2, 5, 10, 20, 50]),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=PRESETS, default="smoke")
    parser.add_argument("--pairs", type=int, nargs="+")
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument("--checkpoints", type=int, nargs="+")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("runs/smoke"))
    parser.add_argument("--aggregate-only", action="store_true")
    args = parser.parse_args()
    config = json.loads((Path(__file__).with_name("config.json")).read_text())
    default_pairs, default_seeds, default_cp = PRESETS[args.preset]
    pairs, seeds, cps = [
        sorted(set(value if value is not None else default))
        for value, default in (
            (args.pairs, default_pairs),
            (args.seeds, default_seeds),
            (args.checkpoints, default_cp),
        )
    ]
    if (
        not pairs
        or not set(pairs) <= set(range(1, 6))
        or not seeds
        or min(seeds) < 0
        or not cps
        or min(cps) < 0
        or args.workers < 1
    ):
        parser.error("Invalid pairs, seeds, checkpoints or workers")
    design = {
        "pairs": pairs,
        "seeds": seeds,
        "checkpoints": cps,
        "config": config,
        "source_sha256": source_hashes(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = args.output / "design.json"
    if manifest.exists() and json.loads(manifest.read_text()) != design:
        parser.error("Configuration/source changed; use a new output directory")
    write_json(manifest, design)
    jobs = [
        (p, c, s)
        for p in config["pairs"]
        if p["id"] in pairs
        for s in seeds
        for c in config["conditions"]
    ]
    if not args.aggregate_only:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {}
            for pair, condition, seed in jobs:
                name = f"p{pair['id']}_{condition['id']}_s{seed}"
                future = executor.submit(
                    run_one, config, pair, condition, seed, cps, args.output / name
                )
                futures[future] = name
            for n, future in enumerate(as_completed(futures), 1):
                print(
                    f"[{n}/{len(jobs)}] {futures[future]}: {future.result()}",
                    flush=True,
                )
    curves = aggregate(args.output, config, len(jobs))
    bootstrap(curves, config, seeds, pairs, cps, args.output)
    print(f"Verified {len(jobs)} runs; {len(curves)} evaluation checkpoints.")


if __name__ == "__main__":
    main()
