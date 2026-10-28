/** Exact full remaining-horizon planning; only self parameters and own table. */
import { actor, context, demand, legal, taskCost, transition } from './environment.js';

export class Predictor {
  constructor(prior = 1) {
    this.prior = prior;
    this.counts = new Map();
    this.version = 0;
  }
  probabilities(state) {
    const actions = legal(state),
      row = this.counts.get(context(state)) || {};
    const denominator =
      actions.reduce((sum, a) => sum + (row[a] || 0), 0) + actions.length * this.prior;
    return Object.fromEntries(actions.map((a) => [a, ((row[a] || 0) + this.prior) / denominator]));
  }
  observe(state, action) {
    const key = context(state),
      row = this.counts.get(key) || {};
    row[action] = (row[action] || 0) + 1;
    this.counts.set(key, row);
    this.version++;
  }
}

export class Planner {
  constructor(id, parameters, enabled, predictor, config) {
    Object.assign(this, { id, parameters, enabled, predictor });
    const keys = [
      'horizon',
      'timeout_penalty',
      'communication_effort',
      'tie_order',
      'tie_tolerance',
    ];
    this.config = Object.fromEntries(keys.map((key) => [key, config[key]]));
    this.memo = new Map();
    this.version = predictor.version;
  }
  total([task, loss]) {
    return task + (this.enabled ? this.parameters.expectation_weight * loss : 0);
  }
  choose(options) {
    const minimum = Math.min(...Object.values(options).map((value) => this.total(value)));
    return this.config.tie_order.find(
      (a) => options[a] && this.total(options[a]) <= minimum + this.config.tie_tolerance,
    );
  }
  value(state) {
    const key = context(state);
    if (this.memo.has(key)) return this.memo.get(key);
    let result;
    if (state.p_A === 'done' && state.p_B === 'done') result = [0, 0];
    else if (state.t >= this.config.horizon)
      result = [
        this.config.timeout_penalty * Number(state[`p_${this.id}`] !== 'done'),
        this.enabled && state.first_yielder === null
          ? demand(state, this.id, this.parameters.delta)
          : 0,
      ];
    else {
      const options = this.candidates(state);
      if (actor(state) === this.id) result = options[this.choose(options)];
      else {
        const q = this.predictor.probabilities(state);
        result = [0, 1].map((k) =>
          Object.keys(options).reduce((sum, a) => sum + q[a] * options[a][k], 0),
        );
      }
    }
    this.memo.set(key, result);
    return result;
  }
  candidate(state, action) {
    const [task, loss] = this.value(transition(state, action));
    const immediateLoss =
      this.enabled && state.first_yielder === null && actor(state) === this.id && action === 'YIELD'
        ? demand(state, this.id, this.parameters.delta)
        : 0;
    return [
      taskCost(state, action, this.id, this.parameters, this.config) + task,
      immediateLoss + loss,
    ];
  }
  candidates(state) {
    return Object.fromEntries(legal(state).map((a) => [a, this.candidate(state, a)]));
  }
  plan(state) {
    if (this.version !== this.predictor.version) {
      this.memo.clear();
      this.version = this.predictor.version;
    }
    const candidates = this.candidates(state);
    return { selected: this.choose(candidates), candidates };
  }
}
