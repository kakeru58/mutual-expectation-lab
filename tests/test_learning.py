from helpers import (
    BaseTests,
    CONFIG,
    IDS,
    META,
    P,
    Planner,
    Predictor,
    State,
    agents_for,
    contexts,
    demand,
    episode,
    legal,
    loss_step,
    replace,
    schedule,
    task_step,
    transition,
)


class Checks(BaseTests):
    def test_T15_eval_frozen(self):
        a = self.agents()
        snapshot = {i: a[i].predictor.export() for i in IDS}
        episode(self.config, a, META, training=False)
        self.assertEqual(snapshot, {i: a[i].predictor.export() for i in IDS})

    def test_T16_reproducible(self):
        def run():
            rows = episode(self.config, self.agents(), META, training=True)
            for r in rows:
                r.pop("planning_seconds")
            return rows

        self.assertEqual(run(), run())

    def test_T17_series_reset(self):
        expected = schedule(self.config, 1, 0, 2)
        for condition in self.config["conditions"]:
            a = self.agents(condition)
            self.assertEqual(a["A"].predictor.counts, {})
            self.assertEqual(schedule(self.config, 1, 0, 2), expected)
        for block in range(2):
            self.assertEqual(
                sorted(cid for b, _, cid in expected if b == block), list(range(12))
            )

    def test_T18_auto_wait(self):
        s = State(t=2, p_A="done", p_B="bay", first_yielder="B")
        agents = self.agents()
        logs = episode(
            self.config, agents, META, initial=s, training=True, forced=["WAIT", "PASS"]
        )
        self.assertTrue(logs[0]["automatic_wait"])
        self.assertEqual(logs[0]["candidates"], {})
        self.assertIsNone(logs[0]["count_update"])
        self.assertFalse(logs[0]["prediction_score"]["included"])

    def test_T19_retraction_cancel_separate(self):
        s = State(r_A=1, c_B=0, u_A=3, u_B=1)
        self.assertEqual(demand(s, "A", P.delta)[0], 0)
        self.assertEqual(s.r_A, 1)
        n = transition(s, "CANCEL")
        self.assertEqual(n.r_A, 0)
        self.assertEqual(demand(n, "A", P.delta), demand(s, "A", P.delta))

    def test_T20_design_counts(self):
        self.assertEqual(len(contexts(CONFIG)), 12)
        runs = (
            len(CONFIG["pairs"])
            * len(CONFIG["conditions"])
            * len(CONFIG["main"]["seeds"])
        )
        self.assertEqual(runs, 300)
        self.assertEqual(runs * (50 * 12 + 12), 183600)
        self.assertEqual(runs * 12, 3600)
        self.assertEqual(3 * (2 * 12 + 12), 108)

    def test_T21_components_policy(self):
        planner = Planner("A", P, 1, Predictor(), self.config)
        s = State(t=16)
        for a, parts in planner.candidates(s).items():
            future = planner.value(transition(s, a))
            self.assertAlmostEqual(parts[0], task_step(s, a, "A", 2, 0.2) + future[0])
            self.assertAlmostEqual(parts[1], loss_step(s, a, "A", 0) + future[1])
        _, rows = planner.plan(s)
        for r in rows.values():
            self.assertAlmostEqual(r["total"], r["task_cost"] + r["expectation_cost"])
        # Frequency revision must invalidate cached values.
        old = planner.value(State(t=17))
        planner.predictor.observe(State(t=17), "WAIT")
        planner.candidates(s)
        self.assertEqual(planner.version, 1)
        self.assertEqual(
            planner.plan(s), Planner("A", P, 1, planner.predictor, self.config).plan(s)
        )

    def test_T22_ability_change(self):
        for condition in CONFIG["conditions"]:
            for pair in CONFIG["pairs"]:
                s = State(t=1, u_A=3, u_B=1, r_A=1)
                self.assertEqual(demand(s, "A", pair["A"]["delta"])[0], 1)
                changed = replace(s, c_B=0)
                self.assertEqual(demand(changed, "A", pair["A"]["delta"])[0], 0)
                self.assertEqual(changed.r_A, 1)
                self.assertNotIn("YIELD", legal(changed))
                a = agents_for(self.config, pair, condition)
                result = episode(self.config, a, META, initial=changed)
                self.assertTrue(all(not r["count_update"] for r in result))
