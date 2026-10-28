import itertools
from helpers import (
    BaseTests,
    IDS,
    META,
    Predictor,
    ROOT,
    State,
    demand,
    episode,
    json,
    legal,
    replace,
    summarize_episode,
    transition,
)


class Checks(BaseTests):
    def test_T01_legal_transitions(self):
        for t in (0, 1):
            for r in (0, 1):
                for cap in (0, 1):
                    s = replace(State(t=t), **{"r_" + IDS[t]: r, "c_" + IDS[t]: cap})
                    expected = {"WAIT", "CANCEL" if r else "REQUEST"} | (
                        {"YIELD"} if cap else set()
                    )
                    self.assertEqual(set(legal(s)), expected)
                    req = transition(s, "CANCEL" if r else "REQUEST")
                    self.assertEqual(req.get("r", s.actor), 1 - r)
                    self.assertEqual(req.p_A, s.p_A)
                    if cap:
                        y = transition(s, "YIELD")
                        self.assertEqual(y.get("p", s.actor), "bay")
                        self.assertEqual((y.r_A, y.r_B), (0, 0))
                        self.assertEqual(y.first_yielder, s.actor)
                        p = transition(y, "PASS")
                        self.assertEqual(p.get("p", y.actor), "done")
                        end = transition(p, "PASS")
                        self.assertEqual((end.p_A, end.p_B), ("done", "done"))
        for pa in ("approach", "bay", "done"):
            for pb in ("approach", "bay", "done"):
                s = State(p_A=pa, p_B=pb)
                self.assertEqual(
                    "PASS" in legal(s),
                    (pa == "approach" and pb in ("bay", "done"))
                    or (pa == "bay" and pb == "done"),
                )
        with self.assertRaises(ValueError):
            transition(State(), "PASS")

    def test_T02_turn_horizon(self):
        logs = self.forced(["WAIT"] * 20)
        self.assertEqual([r["actor"] for r in logs], list("AB" * 10))
        self.assertEqual(logs[-1]["state_after"]["t"], 20)
        self.assertEqual(logs[-1]["termination"], "timeout")

    def test_T03_PASS_time(self):
        r = summarize_episode(self.forced(["YIELD", "PASS", "PASS"]), self.config)
        self.assertEqual((r["arrival_A"], r["arrival_B"]), (3, 2))
        self.assertEqual((r["task_cost_A"], r["task_cost_B"]), (5, 2))

    def test_T04_costs_fixtures(self):
        fixtures = json.loads((ROOT / "tests/fixtures.json").read_text())
        for case in fixtures["cases"]:
            agents = self.agents({"g_A": case["g_A"], "g_B": case["g_B"]})
            r = summarize_episode(
                episode(self.config, agents, META, forced=case["actions"]), self.config
            )
            for key, value in case["expected"].items():
                actual_key = {
                    "capped_arrival_A": "arrival_A",
                    "capped_arrival_B": "arrival_B",
                }.get(key, key)
                actual = r[actual_key]
                if key == "first_yielder" and value is None:
                    actual = actual or None
                self.assertEqual(actual, value, (case["id"], key))

    def test_T05_demand_boundaries(self):
        for delta in (2, 0, -2):
            for ua, ub in itertools.product((1, 3), repeat=2):
                for ca, cb in itertools.product((0, 1), repeat=2):
                    s = State(u_A=ua, u_B=ub, c_A=ca, c_B=cb)
                    self.assertEqual(
                        demand(s, "A", delta)[0],
                        0 if not cb else 1 if not ca else int(ua - ub >= delta),
                    )
                    self.assertEqual(
                        demand(s, "B", delta)[0],
                        0 if not ca else 1 if not cb else int(ub - ua >= delta),
                    )

    def test_T06_probability(self):
        q = Predictor()
        s = State()
        q.counts[s.context()] = {"WAIT": 3, "YIELD": 1, "REQUEST": 1}
        self.assertEqual(q.probabilities(s)["YIELD"], 0.25)
        self.assertNotIn("PASS", q.probabilities(s))

    def test_T07_observer_pre_context(self):
        agents = self.agents()
        episode(
            self.config,
            agents,
            META,
            training=True,
            forced=["REQUEST", "YIELD", "PASS", "PASS"],
        )
        self.assertEqual(
            agents["B"].predictor.counts[State().context()], {"REQUEST": 1}
        )
        self.assertNotIn(State().context(), agents["A"].predictor.counts)
        s = transition(State(), "REQUEST")
        self.assertEqual(agents["A"].predictor.counts[s.context()], {"YIELD": 1})

    def test_T08_request_no_force(self):
        s = transition(State(), "REQUEST")
        self.assertIn("WAIT", legal(s))
        self.assertIn("REQUEST", legal(s))
        n = transition(s, "WAIT")
        self.assertEqual((n.p_A, n.p_B), ("approach", "approach"))
