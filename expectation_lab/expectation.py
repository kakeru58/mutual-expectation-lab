"""Private response criterion; independent of prediction and utterance flags."""

from dataclasses import dataclass
from .environment import other


@dataclass(frozen=True)
class Parameters:
    yield_cost: float
    delta: float
    expectation_weight: float


def demand(s, i, delta):
    if not s.get("c", other(i)):
        return 0, "partner_unable"
    if not s.get("c", i):
        return 1, "self_unable_partner_able"
    return (
        int(s.get("u", i) - s.get("u", other(i)) >= delta),
        "urgency_difference_ge_delta",
    )


def loss_step(s, a, i, delta):
    if s.first_yielder is None and a == "YIELD" and s.actor == i:
        return demand(s, i, delta)[0]
    return 0


def loss_terminal(s, i, delta):
    return demand(s, i, delta)[0] if s.first_yielder is None else 0
