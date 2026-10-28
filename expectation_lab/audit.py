"""Experimenter-only counterfactual L under a task-only selected continuation.

This never feeds back into agent decisions. The planner with g=0 itself does
not read delta or w. External evaluation may apply the held-out criterion.
"""

from functools import lru_cache
from .environment import legal, transition
from .expectation import loss_step, loss_terminal


def counterfactual_candidate_losses(planner, state, delta):
    @lru_cache(None)
    def value(s):
        if s.p_A == s.p_B == "done":
            return 0.0
        if s.t >= planner.config["horizon"]:
            return float(loss_terminal(s, planner.i, delta))
        actions = legal(s)
        if s.actor == planner.i:
            chosen = planner.choose({a: planner._q(s, a) for a in actions})
            return q(s, chosen)
        probabilities = planner.predictor.probabilities(s)
        return sum(probabilities[a] * q(s, a) for a in actions)

    def q(s, action):
        return loss_step(s, action, planner.i, delta) + value(transition(s, action))

    return {a: q(state, a) for a in legal(state)}
