"""One episode: plan, explore, act, observe, update. No experiment orchestration."""

import math
import time
from .environment import State, IDS, ACTIONS, legal, transition, other, task_step
from .expectation import Parameters, demand
from .agent import Agent
from .audit import counterfactual_candidate_losses
from .scheduling import keyed, contexts, schedule


def agents_for(config, pair, condition, predictors=None):
    return {
        i: Agent(
            i,
            Parameters(**pair[i]),
            condition["g_" + i],
            config,
            predictors[i].clone() if predictors else None,
        )
        for i in IDS
    }


def episode(
    config, agents, metadata, context_id=0, training=False, initial=None, forced=None
):
    u, v, c = contexts(config)[context_id]
    s = initial or State(u_A=u, u_B=v, c_A=c[0], c_B=c[1])
    logs = []
    while not s.terminal(config["horizon"]):
        i, j = s.actor, other(s.actor)
        agent, observer = agents[i], agents[j]
        auto = s.get("p", i) == "done"
        before_q = observer.predictor.probabilities(s)
        q_all = {a: before_q.get(a, 0.0) for a in ACTIONS}
        started = time.perf_counter()
        if auto:
            selected, candidates = "WAIT", {}
        else:
            selected, candidates = agent.planner.plan(s)
            if not agent.g:
                # Experimenter calculation after decision; never an agent input.
                losses = counterfactual_candidate_losses(
                    agent.planner, s, agent.parameters.delta
                )
                for a in candidates:
                    candidates[a]["loss"] = losses[a]
                    candidates[a]["loss_role"] = "counterfactual_evaluator_only"
            else:
                for a in candidates:
                    candidates[a]["loss_role"] = "active_criterion"
        planning_seconds = time.perf_counter() - started
        key = (
            metadata["pair_id"],
            metadata["seed"],
            metadata.get("block", -1),
            metadata["episode_id"],
            s.t,
            i,
        )
        explore = (
            not auto
            and training
            and keyed(*key, "explore").random() < config["epsilon_train"]
        )
        action = keyed(*key, "explore_action").choice(legal(s)) if explore else selected
        if forced is not None:
            action, explore = forced[len(logs)], False
        ds = {k: demand(s, k, agents[k].parameters.delta) for k in IDS}
        task = {
            k: task_step(
                s,
                action,
                k,
                agents[k].parameters.yield_cost,
                config["communication_effort"],
            )
            for k in IDS
        }
        loss = {k: None for k in IDS}
        expectation_cost = {k: 0.0 for k in IDS}
        resolved = s.first_yielder is None and action == "YIELD"
        if resolved:
            loss = {k: ds[k][0] if k == i else 0 for k in IDS}
        nxt = transition(s, action)
        normal = nxt.p_A == nxt.p_B == "done"
        timeout = not normal and nxt.t >= config["horizon"]
        if timeout:
            for k in IDS:
                if nxt.get("p", k) != "done":
                    task[k] += config["timeout_penalty"]
            if nxt.first_yielder is None:
                loss = {k: ds[k][0] for k in IDS}
        if any(v is not None for v in loss.values()):
            expectation_cost = {
                k: agents[k].g * agents[k].parameters.expectation_weight * loss[k]
                for k in IDS
            }
        update = (
            observer.predictor.observe(s, action) if training and not auto else None
        )
        included = not auto and len(legal(s)) > 1
        prediction_score = {
            "included": included,
            "excluded_reason": (
                None
                if included
                else ("automatic_WAIT" if auto else "single_legal_action")
            ),
            "log_loss": -math.log(q_all[action]) if included else None,
            "brier": (
                sum((q_all[a] - int(a == action)) ** 2 for a in ACTIONS)
                if included
                else None
            ),
        }
        expect_display = {}
        for k in IDS:
            active = s.first_yielder is None
            expect_display[k] = {
                "g": agents[k].g,
                "d": ds[k][0] if agents[k].g and active else None,
                "reason": (
                    ds[k][1]
                    if agents[k].g and active
                    else "disabled" if not agents[k].g else "inactive"
                ),
                "active": bool(active and agents[k].g),
                "w": agents[k].parameters.expectation_weight if agents[k].g else None,
            }
        logs.append(
            {
                **metadata,
                "context_id": context_id,
                "t": s.t,
                "actor": i,
                "state_before": s.public(),
                "state_after": nxt.public(),
                "input_observation": {
                    "public": s.public(),
                    "self_parameters": {
                        "yield_cost": agent.parameters.yield_cost,
                        **(
                            {
                                "delta": agent.parameters.delta,
                                "expectation_weight": agent.parameters.expectation_weight,
                            }
                            if agent.g
                            else {}
                        ),
                    },
                    "own_predictor_version": agent.predictor.version,
                },
                "legal_actions": list(legal(s)),
                "candidates": candidates,
                "selected": selected,
                "executed": action,
                "exploration": explore,
                "automatic_wait": auto,
                "q_observer": j,
                "q": q_all,
                "count_update": update,
                "expectation": expect_display,
                "evaluation_only": {
                    "parameters": {k: vars(agents[k].parameters) for k in IDS},
                    "counterfactual_d": {k: ds[k][0] for k in IDS},
                    "settlement_d": (
                        {k: ds[k][0] for k in IDS}
                        if any(v is not None for v in loss.values())
                        else None
                    ),
                },
                "request_flags": {k: s.get("r", k) for k in IDS},
                "settlement": (
                    "yield"
                    if resolved
                    else "timeout" if timeout and nxt.first_yielder is None else None
                ),
                "L": loss,
                "task_increment": task,
                "expectation_increment": expectation_cost,
                "prediction_score": prediction_score,
                "termination": "success" if normal else "timeout" if timeout else None,
                "planning_seconds": planning_seconds,
            }
        )
        s = nxt
    return logs
