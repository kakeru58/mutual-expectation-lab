/** A fresh session starts with two empty tables. No saved policy is loaded. */
import {
  actor,
  context,
  demand,
  initial,
  legal,
  other,
  terminal,
  taskCost,
  transition,
} from './environment.js';
import { Planner, Predictor } from './planner.js';
import { keyed } from './random.js';

export function contexts(config) {
  return config.urgencies.flatMap((a) =>
    config.urgencies.flatMap((b) => config.capability_patterns.map(([ca, cb]) => [a, b, ca, cb])),
  );
}

export class Session {
  constructor(config, pairId, conditionId, seed) {
    this.config = config;
    this.pair = config.pairs.find((pair) => pair.id === pairId);
    this.condition = config.conditions.find((c) => c.id === conditionId);
    this.seed = seed;
    this.completed = 0;
    this.agents = Object.fromEntries(
      ['A', 'B'].map((id) => {
        const predictor = new Predictor(config.prior_count);
        return [
          id,
          {
            predictor,
            planner: new Planner(id, this.pair[id], this.condition[`g_${id}`], predictor, config),
          },
        ];
      }),
    );
  }
  status() {
    return {
      completed: this.completed,
      blocks: Math.floor(this.completed / 12),
      counts: Object.fromEntries(['A', 'B'].map((i) => [i, this.agents[i].predictor.version])),
    };
  }
  async episode({ training = true, contextId = 0 } = {}) {
    const block = Math.floor(this.completed / 12),
      slot = this.completed % 12;
    const order = (await keyed(this.pair.id, this.seed, block, 'context_order')).shuffle(
      Array.from({ length: 12 }, (_, i) => i),
    );
    const cid = training ? order[slot] : contextId,
      scene = contexts(this.config)[cid];
    let state = initial(...scene);
    const steps = [],
      before = this.status();
    while (!terminal(state, this.config.horizon)) {
      const i = actor(state),
        j = other(i),
        automatic = state[`p_${i}`] === 'done';
      const { selected, candidates } = automatic
        ? { selected: 'WAIT', candidates: {} }
        : this.agents[i].planner.plan(state);
      const key = [this.pair.id, this.seed, block, this.completed, state.t, i];
      const exploration =
        training &&
        !automatic &&
        (await keyed(...key, 'explore')).random() < this.config.epsilon_train;
      const executed = exploration
        ? (await keyed(...key, 'explore_action')).choice(legal(state))
        : selected;
      const q = this.agents[j].predictor.probabilities(state);
      const d = Object.fromEntries(
        ['A', 'B'].map((id) => [id, demand(state, id, this.pair[id].delta)]),
      );
      const task = Object.fromEntries(
        ['A', 'B'].map((id) => [id, taskCost(state, executed, id, this.pair[id], this.config)]),
      );
      const loss = { A: null, B: null };
      if (state.first_yielder === null && executed === 'YIELD') {
        loss[i] = d[i];
        loss[j] = 0;
      }
      const next = transition(state, executed);
      const success = next.p_A === 'done' && next.p_B === 'done';
      const timeout = !success && next.t >= this.config.horizon;
      if (timeout) {
        for (const id of ['A', 'B']) {
          if (next[`p_${id}`] !== 'done') task[id] += this.config.timeout_penalty;
          if (next.first_yielder === null) loss[id] = d[id];
        }
      }
      if (training && !automatic) this.agents[j].predictor.observe(state, executed);
      const expectationCost = Object.fromEntries(
        ['A', 'B'].map((id) => [
          id,
          loss[id] === null
            ? 0
            : this.condition[`g_${id}`] * this.pair[id].expectation_weight * loss[id],
        ]),
      );
      steps.push({
        state_before: state,
        state_after: next,
        actor: i,
        executed,
        selected,
        candidates,
        exploration,
        automatic_wait: automatic,
        q,
        observer: j,
        d,
        task_increment: task,
        expectation_increment: expectationCost,
        loss,
        termination: success ? 'success' : timeout ? 'timeout' : null,
      });
      state = next;
    }
    if (training) this.completed++;
    return { before, after: this.status(), context_id: cid, steps };
  }
}
