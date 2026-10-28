[English](README.md) | [日本語](README.ja.md)

# Mutual Expectation Lab

[Browser tool](https://kakeru58.github.io/mutual-expectation-lab/) | [Repository](https://github.com/kakeru58/mutual-expectation-lab)

A two-agent yielding task with separate partner-action prediction and response-evaluation costs.

The Python package is the research implementation. The browser tool runs the same model from epoch 0. Reference summaries cover five pairs, three conditions and 20 seeds.

## Run the model

Python 3.11 or later; reference environment: Python 3.12.8. No runtime dependencies.

```sh
python3 -m unittest discover -s tests -v
python3 -m expectation_lab --preset smoke --output runs/smoke
```

## Open the browser tool

```sh
python3 -m http.server 8000 --directory docs
```

Open [localhost:8000](http://localhost:8000). The tool requires HTTP or HTTPS, not direct file access.

The header button switches between English and Japanese. Switching language preserves training data and playback position. Only the language preference is saved.

- **Training:** shows completed epochs, total episodes and progress within the current epoch. One epoch has 12 scenarios.
- **Train until epoch:** an absolute target. Training from epoch 2 to epoch 5 adds 36 episodes.
- **Evaluation:** runs a selected scenario without exploration or learning.
- **Reset to epoch 0:** clears both prediction tables. Changing pair, condition or seed also resets training.

Requests and cancellations appear as messages. Movement and waiting appear as actions. Archived results are separate from the live session.

## Reproduce the full experiment

```sh
python3 -m expectation_lab --preset curves --workers 3 --output runs/full
python3 tools/compare_results.py --run runs/full
```

This runs 201,600 episodes with evaluations at epochs 0, 2, 5, 10, 20 and 50. Completed runs are preserved; use the same command to resume, or a new output directory to start over.

For a smaller trial, add `--pairs 1 3 4 --seeds 0` and choose a separate output directory.

## Read the code

The model modules in `expectation_lab/` are each under 200 lines. Read them in this order:

| File | Responsibility |
|---|---|
| `environment.py` | State, legal actions and transitions |
| `prediction.py` | Partner action counts and probabilities |
| `expectation.py` | Demands and fulfillment loss |
| `planner.py` | Full remaining-horizon planning |
| `simulation.py` | One episode |
| `experiment.py` | Training and frozen checkpoint evaluations |

## Documentation and tests

[METHOD.md](METHOD.md) contains the model, experiment design, statistical definitions and detailed reproduction commands. Third-party notices are in [THIRD_PARTY.md](THIRD_PARTY.md).

Browser tests require development dependencies:

```sh
npm ci --ignore-scripts
npm test
```

The repository includes code, settings, tests and reference summaries. Generated runs, local development records and raw working documents are excluded from the distribution.

## Publish with GitHub Pages

1. Push this folder to the repository's `main` branch.
2. Set **Settings > Pages > Source** to **GitHub Actions**.
3. Run **Actions > Publish demo to GitHub Pages** and open the URL it returns.

The workflow also runs on pushes to `main`. Only `docs/` is served; it uses relative URLs and a browser-side Web Worker, with no external API or Python server. The header language switch is available on all three pages.

A project reuse license has not been selected; the MT19937 license notice is retained in `THIRD_PARTY.md`.
