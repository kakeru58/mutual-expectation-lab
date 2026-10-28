"""An observer's frequency table over exact public pre-action states."""

from copy import deepcopy
from .environment import legal


class Predictor:
    def __init__(self, prior=1):
        self.counts = {}
        self.prior = prior
        self.version = 0

    def probabilities(self, s):
        actions = legal(s)
        counts = self.counts.get(s.context(), {})
        denom = sum(counts.get(a, 0) for a in actions) + len(actions) * self.prior
        return {a: (counts.get(a, 0) + self.prior) / denom for a in actions}

    def observe(self, s, action):
        if action not in legal(s):
            raise ValueError(action)
        row = self.counts.setdefault(s.context(), {})
        before = dict(row)
        row[action] = row.get(action, 0) + 1
        self.version += 1
        return {
            "context": list(s.context()),
            "before": before,
            "after": dict(row),
            "version": self.version,
        }

    def clone(self):
        return deepcopy(self)

    def export(self):
        return {
            "version": self.version,
            "prior": self.prior,
            "rows": [
                {"context": list(k), "counts": v}
                for k, v in sorted(self.counts.items(), key=lambda x: repr(x[0]))
            ],
        }
