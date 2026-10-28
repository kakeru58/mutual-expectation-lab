import itertools
from helpers import (
    BaseTests,
    META,
    P,
    Parameters,
    Planner,
    Predictor,
    State,
    TaskOnlyReference,
    contexts,
    episode,
    replace,
    summarize_episode,
)


class Checks(BaseTests):
    def test_T09_reference_and_zero_weight(self):
        q = Predictor()
        for t in range(16, 20):
            for cid, (u, v, c) in enumerate(contexts(self.config)):
                s = State(t=t, u_A=u, u_B=v, c_A=c[0], c_B=c[1])
                i = s.actor
                ref = TaskOnlyReference(i, P, 0, q, self.config).plan(s)
                for g, p in ((0, P), (1, replace(P, expectation_weight=0))):
                    result = Planner(i, p, g, q, self.config).plan(s)
                    self.assertEqual(ref[0], result[0])
                    for a in ref[1]:
                        self.assertAlmostEqual(
                            ref[1][a]["total"], result[1][a]["total"]
                        )

    def test_T10_pre_yield_d_preserved(self):
        logs = self.forced(["YIELD", "PASS", "PASS"])
        self.assertEqual(logs[0]["L"]["A"], 1)
        self.assertEqual(logs[1]["expectation"]["A"]["reason"], "inactive")

    def test_T11_once(self):
        logs = self.forced(["YIELD"] + ["WAIT"] * 19)
        self.assertEqual(sum(r["expectation_increment"]["A"] for r in logs), 6)
        self.assertEqual(sum(r["L"]["A"] is not None for r in logs), 1)

    def test_T12_timeouts(self):
        unresolved = summarize_episode(self.forced(["WAIT"] * 20), self.config)
        resolved = summarize_episode(
            self.forced(["YIELD"] + ["WAIT"] * 19), self.config
        )
        self.assertEqual(unresolved["expectation_cost_B"], 6)
        self.assertEqual(resolved["expectation_cost_B"], 0)
        self.assertEqual(resolved["task_cost_A"], 122)
        # Normal completion at t=20 takes precedence over timeout.
        s = State(t=19, p_A="done", p_B="bay", first_yielder="B")
        r = episode(self.config, self.agents(), META, initial=s, forced=["PASS"])[-1]
        self.assertEqual(r["termination"], "success")
        self.assertEqual(r["task_increment"]["B"], 1)

    def test_T13_private_isolation(self):
        a = self.agents()
        before = a["A"].planner.plan(State())
        a["B"].parameters = Parameters(999, -999, 999)
        a["B"].predictor.counts[State().context()] = {"WAIT": 999}
        self.assertEqual(before, a["A"].planner.plan(State()))
        self.assertFalse(hasattr(a["A"].planner, "partner"))
        self.assertNotIn("pairs", a["A"].planner.config)
        self.assertNotIn("conditions", a["A"].planner.config)
        self.assertEqual(
            set(vars(a["A"].planner)) & {"agents", "pair", "partner_parameters"}, set()
        )

    def test_T14_exhaustive_agrees(self):
        for remaining in range(1, 5):
            for u, v, c in contexts(self.config):
                for rA, rB in itertools.product((0, 1), repeat=2):
                    s = State(
                        t=20 - remaining,
                        u_A=u,
                        u_B=v,
                        c_A=c[0],
                        c_B=c[1],
                        r_A=rA,
                        r_B=rB,
                    )
                    q = Predictor()
                    q.observe(s, "WAIT")
                    for g in (0, 1):
                        dp = Planner(s.actor, P, g, q, self.config)
                        tree = Planner(s.actor, P, g, q, self.config, memoize=False)
                        self.assertEqual(dp.plan(s), tree.plan(s))
