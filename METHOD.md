[English](METHOD.md) | [日本語](METHOD.ja.md)

# Method and reproduction

## Environment and learning

The public state is `(t, p_A, p_B, u_A, u_B, c_A, c_B, r_A, r_B, first_yielder)`. Positions are approach, bay or done; u is urgency, c is yielding ability and r is a pending spoken request. A acts first, turns alternate, and the episode ends after both arrivals or 20 turns.

`environment.py` defines legal actions and transitions. An agent in a bay waits for the partner to pass. REQUEST does not force a response; CANCEL withdraws a pending request without changing the demand criterion.

Each agent learns its partner's action counts for the exact public context before an action:

```
q_i(a | x) = (n_i(x,a) + 1) / (sum_legal n_i(x,b) + K)
```

Only partner observations update the table. Automatic WAIT by an arrived agent is excluded. Time and request-flag differences are not merged. Training explores uniformly over legal actions with probability 0.1; evaluation uses neither exploration nor updates.

Epoch 0 means no observed behavior from this partner: both tables are empty and legal actions have uniform prior probabilities. The environment rules and public urgency and ability are still known. Later epochs accumulate experience with the same partner. Population-level social priors, partner switching and uncertain identity are outside this protocol.

## Parameters, demands and costs

Each agent has fixed yielding cost k, demand threshold delta and expectation weight w. Demand d is zero if the partner cannot yield, one if only the partner can yield, and otherwise `d_i = 1[u_i - u_j >= delta_i]`.

| Pair | A: k / delta / w | B: k / delta / w |
|---|---|---|
| 1 | 2 / 2 / 2 | 2 / 2 / 2 |
| 2 | 2 / 0 / 6 | 2 / 2 / 2 |
| 3 | 2 / 0 / 6 | 2 / 0 / 6 |
| 4 | 6 / 0 / 6 | 1 / 0 / 6 |
| 5 | 2 / -2 / 8 | 2 / 2 / 2 |

These parameters do not change through learning. Pending requests r and internal demands d are distinct.

An unarrived agent pays urgency u on every turn, including its arrival turn. Its own YIELD adds k; its own REQUEST or CANCEL adds 0.2. An unarrived timeout adds 100.

At the first YIELD, the yielding agent's loss L is its demand immediately before the action; the partner's loss is zero. An unresolved timeout uses the terminal demand. Loss is charged once, and is not charged again after priority has been settled.

## Conditions and planning

```
J_i = E[C_task,i] + g_i * w_i * E[L_i]
Q_i(s,a) = c_task,i + g_i * w_i * c_loss,i + V_i(F(s,a))
```

Conditions are P_P=(0,0), E_P=(1,0) and E_E=(1,1); only g changes. `planner.py` minimizes on self turns and averages over a frozen partner prediction q on partner turns. Task and loss components follow the same selected continuation policy.

Planning covers every remaining turn without anticipating future learning, exploration or unannounced changes. Ties within 1e-9 use PASS, YIELD, WAIT, REQUEST, CANCEL. The planner retains only self parameters, its own prediction table and public planning constants; it receives no partner parameter table or partner g.

`audit.py` computes counterfactual L for disabled expectations after the decision, without feedback into behavior. The browser omits this audit while preserving action choice and objective costs. Exact context tuples, bounded transition caches and prediction-versioned value caches improve performance without shortening the horizon or merging contexts.

This operationalizes an explicit evaluation of the response sought from another agent. It does not establish psychological validity or irreducibility to preferences.

## Experimental design and analysis

- Five parameter pairs, three conditions and seeds 0 through 19: 300 runs.
- One epoch: four urgency combinations and three ability combinations, giving 12 scenarios.
- Each run trains with a fixed partner for 50 epochs. Both agents learn; scenario order and exploration keys are shared across conditions.
- At epochs 0, 2, 5, 10, 20 and 50, copied prediction tables evaluate all 12 scenarios without exploration or updates. Evaluation does not affect subsequent training.

The total is 180,000 training plus 21,600 evaluation episodes: 201,600 episodes. The final-checkpoint-only preset contains 183,600 episodes.

Primary outcomes are joint arrival rate and joint task cost. Communication measures count REQUEST/CANCEL and episodes with at least one such action. Expectation-inclusive objective cost is not a social performance measure. Prediction log loss and Brier score exclude automatic WAIT and single-legal-action cases; their observed-action distributions may differ across conditions and stages.

Each pair/seed/condition/checkpoint averages the 12 scenarios equally. E_P minus P_P and E_E minus E_P are paired by seed. Bootstrap resamples seeds 10,000 times with common indices across pairs, conditions and checkpoints; the all-pair summary weights pairs equally. Pointwise 95% percentile intervals describe simulation-seed variation, not human populations, and have no multiple-comparison correction. Reduced communication alone does not establish improvement or overfitting.

## Reproduction

The reference environment is CPython 3.12.8. Experiments and statistics use the standard library. Browser tests use the locked Node.js development dependencies.

```sh
python3 -m unittest discover -s tests -v
npm ci --ignore-scripts
npm test
python3 -m expectation_lab --preset curves --workers 3 --output runs/full
python3 tools/compare_results.py --run runs/full
```

Expected output: 300 runs and 1,800 pair/seed/condition/checkpoint summaries. All reference rows matched exactly in the reference environment; other Python versions may differ in final floating-point digits. Tests cover independent exhaustive planning, costs, information boundaries, learning, frozen evaluation, log reconstruction, resumption, browser/Python agreement and UI behavior.

Completed runs are preserved. Repeat the same command to resume; change the output directory to start over. Changed settings or source hashes require a new directory. For aggregation only, repeat the same preset and options with `--aggregate-only`. Workers process independent runs without changing the model.

### Statistics and figures

```sh
python3 tools/paper_statistics.py --run runs/full
python3 -m venv .venv-plot
.venv-plot/bin/python -m pip install -r requirements-plot.txt
.venv-plot/bin/python tools/plot_curves.py --run runs/full
```

`paper_stats/` contains the published five-metric intervals, paired contrasts, communication patterns and bootstrap settings. Communication counts are per 12 evaluation episodes. The compact `paired_contrasts.csv` at the run root instead contains three metrics and communication per episode; use `paper_stats/` for comparison with the published tables.

The figure command writes PNG, SVG and PDF to the run directory. Generate statistics first to include confidence bands. Checkpoints are equally spaced; pixel rendering may vary across platforms.

### Outputs

| File | Content |
|---|---|
| `docs/data/config.json` | Published settings; identical to `expectation_lab/config.json` |
| `docs/data/curves.csv` | Reference per-seed evaluation summaries |
| `docs/data/curve_intervals.csv` | Reference means and pointwise intervals |
| `docs/data/paired_contrasts.csv` | Reference paired condition differences |
| `docs/data/communication_patterns.csv` | Reference communication patterns |
| `runs/full/*/steps.jsonl.gz` | Generated step logs |
| `runs/full/*/predictors_b*.json` | Generated checkpoint prediction tables |
| `runs/full/design.json` | Run settings and source hashes |

Stored episode summaries are checked against raw logs. Generated runs and local development records are excluded from the distribution. Test fixtures support independent checks; the live demo never loads archived training results or test fixtures. These are computational results, not human-subject data.
