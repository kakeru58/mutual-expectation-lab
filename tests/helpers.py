import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path
from expectation_lab.environment import IDS, State, legal, transition, task_step
from expectation_lab.expectation import Parameters, demand, loss_step
from expectation_lab.prediction import Predictor
from expectation_lab.planner import Planner, TaskOnlyReference
from expectation_lab.simulation import agents_for, contexts, episode, schedule
from expectation_lab.metrics import summarize_episode

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "expectation_lab/config.json").read_text())
P = Parameters(2, 0, 6)
META = dict(
    run_id="test", pair_id=1, condition="E_E", seed=0, phase="train", episode_id=0
)


class BaseTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(CONFIG)
        self.pair = {"id": 1, "A": vars(P).copy(), "B": vars(P).copy()}
        self.condition = CONFIG["conditions"][2]

    def agents(self, condition=None):
        return agents_for(self.config, self.pair, condition or self.condition)

    def forced(self, actions, **kwargs):
        return episode(self.config, self.agents(), META, forced=actions, **kwargs)
