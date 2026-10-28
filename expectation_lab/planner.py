"""Exact remaining-horizon DP. Receives only self parameters and own predictor."""

from functools import lru_cache
from .environment import legal, transition, task_step
from .expectation import demand, loss_step, loss_terminal


class Planner:
    def __init__(self, i, parameters, g, predictor, config, memoize=True):
        self.i, self.parameters, self.g = i, parameters, g
        self.predictor = predictor
        # Retain only public planning constants, never the experiment's pair table.
        keys = (
            "horizon",
            "timeout_penalty",
            "communication_effort",
            "tie_order",
            "tie_tolerance",
        )
        self.config = {key: config[key] for key in keys}
        self.version = predictor.version
        self.memoize = memoize
        self.visits = 0
        self.value = lru_cache(None)(self._value) if memoize else self._value

    def _check(self):
        if self.version != self.predictor.version:
            self.version = self.predictor.version
            if self.memoize:
                self.value.cache_clear()

    def total(self, parts):
        # Disabled expectations never consult private delta/weight in planning.
        return parts[0] + (
            self.g * self.parameters.expectation_weight * parts[1] if self.g else 0
        )

    def choose(self, candidates):
        best = min(self.total(v) for v in candidates.values())
        return next(
            a
            for a in self.config["tie_order"]
            if a in candidates
            and self.total(candidates[a]) <= best + self.config["tie_tolerance"]
        )

    def _value(self, s):
        self.visits += 1
        if s.p_A == s.p_B == "done":
            return (0.0, 0.0)
        if s.t >= self.config["horizon"]:
            return (
                self.config["timeout_penalty"] * (s.get("p", self.i) != "done"),
                loss_terminal(s, self.i, self.parameters.delta) if self.g else 0.0,
            )
        options = {a: self._q(s, a) for a in legal(s)}
        if s.actor == self.i:
            return options[self.choose(options)]
        probs = self.predictor.probabilities(s)
        return tuple(sum(probs[a] * options[a][k] for a in options) for k in (0, 1))

    def _q(self, s, a):
        future = self.value(transition(s, a))
        task = task_step(
            s,
            a,
            self.i,
            self.parameters.yield_cost,
            self.config["communication_effort"],
        )
        loss = loss_step(s, a, self.i, self.parameters.delta) if self.g else 0
        return (task + future[0], loss + future[1])

    def candidates(self, s):
        self._check()
        return {a: self._q(s, a) for a in legal(s)}

    def plan(self, s):
        if s.actor != self.i:
            raise ValueError("Planner called on partner turn")
        parts = self.candidates(s)
        selected = self.choose(parts)
        rows = {
            a: {
                "task_cost": v[0],
                "loss": v[1],
                "expectation_cost": self.total(v) - v[0],
                "total": self.total(v),
            }
            for a, v in parts.items()
        }
        return selected, rows


class TaskOnlyReference(Planner):
    """Independently evaluated scalar task-only recursion for equivalence tests."""

    def _value(self, s):
        if s.p_A == s.p_B == "done":
            return (0.0, 0.0)
        if s.t >= self.config["horizon"]:
            return (
                self.config["timeout_penalty"] * (s.get("p", self.i) != "done"),
                0.0,
            )
        costs = {
            a: task_step(
                s,
                a,
                self.i,
                self.parameters.yield_cost,
                self.config["communication_effort"],
            )
            + self.value(transition(s, a))[0]
            for a in legal(s)
        }
        if s.actor == self.i:
            m = min(costs.values())
            chosen = next(
                a
                for a in self.config["tie_order"]
                if a in costs and costs[a] <= m + self.config["tie_tolerance"]
            )
            return costs[chosen], 0.0
        q = self.predictor.probabilities(s)
        return sum(q[a] * costs[a] for a in costs), 0.0

    def _q(self, s, a):
        return (
            task_step(
                s,
                a,
                self.i,
                self.parameters.yield_cost,
                self.config["communication_effort"],
            )
            + self.value(transition(s, a))[0],
            0.0,
        )
