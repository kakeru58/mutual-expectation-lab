"""Public state, legal actions and deterministic physical transitions only."""

from dataclasses import dataclass, fields, replace
from functools import lru_cache

ACTIONS = ("PASS", "YIELD", "WAIT", "REQUEST", "CANCEL")
IDS = ("A", "B")


@dataclass(frozen=True, slots=True)
class State:
    t: int = 0
    p_A: str = "approach"
    p_B: str = "approach"
    u_A: int = 1
    u_B: int = 1
    c_A: int = 1
    c_B: int = 1
    r_A: int = 0
    r_B: int = 0
    first_yielder: str | None = None

    @property
    def actor(self):
        return IDS[self.t % 2]

    def get(self, prefix, i):
        return getattr(self, prefix + "_" + i)

    def context(self):
        # Exact public context; avoid recursive dataclasses.asdict in every DP node.
        return (
            self.t,
            self.p_A,
            self.p_B,
            self.u_A,
            self.u_B,
            self.c_A,
            self.c_B,
            self.r_A,
            self.r_B,
            self.first_yielder,
        )

    def public(self):
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def terminal(self, horizon):
        return (self.p_A == self.p_B == "done") or self.t >= horizon


def other(i):
    return "B" if i == "A" else "A"


@lru_cache(maxsize=32768)
def legal(s):
    i, j = s.actor, other(s.actor)
    p, q = s.get("p", i), s.get("p", j)
    if p == "done":
        return ("WAIT",)
    actions = {"WAIT"}
    if p == q == "approach":
        if s.get("c", i):
            actions.add("YIELD")
        if not s.get("r", i):
            actions.add("REQUEST")
    if (p == "approach" and q in ("bay", "done")) or (p == "bay" and q == "done"):
        actions.add("PASS")
    if s.get("r", i):
        actions.add("CANCEL")
    return tuple(a for a in ACTIONS if a in actions)


@lru_cache(maxsize=65536)
def transition(s, a):
    if a not in legal(s):
        raise ValueError(f"illegal {a}: {s}")
    changes = {"t": s.t + 1}
    if a == "PASS":
        changes["p_" + s.actor] = "done"
    if a == "YIELD":
        changes.update(
            {"p_" + s.actor: "bay", "first_yielder": s.actor, "r_A": 0, "r_B": 0}
        )
    if a in ("REQUEST", "CANCEL"):
        changes["r_" + s.actor] = int(a == "REQUEST")
    return replace(s, **changes)


def task_step(s, a, i, yield_cost, communication_effort):
    cost = s.get("u", i) if s.get("p", i) != "done" else 0
    if s.actor == i:
        cost += yield_cost if a == "YIELD" else 0
        cost += communication_effort if a in ("REQUEST", "CANCEL") else 0
    return cost
