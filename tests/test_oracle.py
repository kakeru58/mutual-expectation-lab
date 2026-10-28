"""Independent tree oracle, counterfactual audit, terminal and logging checks."""

import json
import unittest
from pathlib import Path
from expectation_lab.environment import State, legal, transition, task_step
from expectation_lab.expectation import Parameters, demand
from expectation_lab.prediction import Predictor
from expectation_lab.planner import Planner
from expectation_lab.audit import counterfactual_candidate_losses

CONFIG = json.loads(
    (Path(__file__).resolve().parents[1] / "expectation_lab/config.json").read_text()
)


class IndependentChecks(unittest.TestCase):
    def test_full_tree_oracle_nonuniform(self):
        for remaining in range(1, 5):
            for who in ("A", "B"):
                for g in (0, 1):
                    start = State(t=20 - remaining, u_A=3, u_B=1, r_A=1)
                    p = Parameters(2, 0, 6)
                    q = Predictor()
                    frontier = [start]
                    seen = set()
                    while frontier:
                        s = frontier.pop()
                        if s in seen or s.terminal(20):
                            continue
                        seen.add(s)
                        q.counts[s.context()] = {
                            a: (s.t + idx * 3 + s.r_A) % 7
                            for idx, a in enumerate(legal(s))
                        }
                        frontier.extend(transition(s, a) for a in legal(s))

                    # No memoization, no calls to Planner value/transition cost decomposition.
                    def tree(s):
                        if s.p_A == s.p_B == "done":
                            return 0.0, 0.0
                        if s.t == 20:
                            return (
                                100.0 * (s.get("p", who) != "done"),
                                (
                                    float(demand(s, who, p.delta)[0])
                                    if g and s.first_yielder is None
                                    else 0.0
                                ),
                            )
                        choices = {a: branch(s, a) for a in legal(s)}
                        if s.actor == who:
                            scores = {
                                a: t + g * p.expectation_weight * l
                                for a, (t, l) in choices.items()
                            }
                            best = min(scores.values())
                            chosen = next(
                                a
                                for a in CONFIG["tie_order"]
                                if a in scores and scores[a] <= best + 1e-9
                            )
                            return choices[chosen]
                        probs = q.probabilities(s)
                        return tuple(
                            sum(probs[a] * choices[a][k] for a in choices)
                            for k in (0, 1)
                        )

                    def branch(s, a):
                        ft, fl = tree(transition(s, a))
                        immediate = s.get("u", who) if s.get("p", who) != "done" else 0
                        if s.actor == who:
                            immediate += (
                                2
                                if a == "YIELD"
                                else 0.2 if a in ("REQUEST", "CANCEL") else 0
                            )
                        loss = (
                            demand(s, who, p.delta)[0]
                            if g
                            and s.actor == who
                            and a == "YIELD"
                            and s.first_yielder is None
                            else 0
                        )
                        return immediate + ft, loss + fl

                    planner = Planner(who, p, g, q, CONFIG)
                    for a, parts in planner.candidates(start).items():
                        expected = branch(start, a)
                        for x, y in zip(parts, expected):
                            self.assertAlmostEqual(x, y, places=11)

    def test_counterfactual_loss_does_not_change_choice(self):
        s = State(t=17)
        p = Parameters(2, 0, 6)
        planner = Planner("B", p, 0, Predictor(), CONFIG)
        before = planner.plan(s)
        losses = counterfactual_candidate_losses(planner, s, 0)
        self.assertEqual(losses["YIELD"], 1)
        self.assertTrue(all(0 <= v <= 1 for v in losses.values()))
        self.assertEqual(before, planner.plan(s))

    def test_all_reachable_transition_invariants(self):
        frontier = [State()]
        seen = set()
        while frontier:
            s = frontier.pop()
            if s in seen or s.t >= 6 or s.terminal(20):
                continue
            seen.add(s)
            for a in legal(s):
                n = transition(s, a)
                self.assertEqual(n.t, s.t + 1)
                self.assertEqual(n.actor, "B" if s.actor == "A" else "A")
                self.assertEqual(
                    n.get("p", "B" if s.actor == "A" else "A"),
                    s.get("p", "B" if s.actor == "A" else "A"),
                )
                if a == "YIELD":
                    self.assertIsNone(s.first_yielder)
                    self.assertEqual(n.first_yielder, s.actor)
                    self.assertEqual((n.r_A, n.r_B), (0, 0))
                else:
                    self.assertEqual(n.first_yielder, s.first_yielder)
                frontier.append(n)
        self.assertGreater(len(seen), 30)
