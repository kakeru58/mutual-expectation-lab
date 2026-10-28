from .prediction import Predictor
from .planner import Planner


class Agent:
    def __init__(self, i, parameters, g, config, predictor=None):
        self.i, self.parameters, self.g = i, parameters, g
        self.predictor = (
            predictor if predictor is not None else Predictor(config["prior_count"])
        )
        self.planner = Planner(i, parameters, g, self.predictor, config)
