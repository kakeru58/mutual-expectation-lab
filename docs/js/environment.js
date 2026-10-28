/** Public environment. This file knows no private partner parameters. */
export const ACTIONS = ['PASS', 'YIELD', 'WAIT', 'REQUEST', 'CANCEL'];
export const other = (id) => (id === 'A' ? 'B' : 'A');
export const actor = (state) => (state.t % 2 === 0 ? 'A' : 'B');
export const initial = (uA, uB, cA, cB) => ({
  t: 0,
  p_A: 'approach',
  p_B: 'approach',
  u_A: uA,
  u_B: uB,
  c_A: cA,
  c_B: cB,
  r_A: 0,
  r_B: 0,
  first_yielder: null,
});
export const context = (s) =>
  JSON.stringify([s.t, s.p_A, s.p_B, s.u_A, s.u_B, s.c_A, s.c_B, s.r_A, s.r_B, s.first_yielder]);
export const terminal = (s, horizon) => (s.p_A === 'done' && s.p_B === 'done') || s.t >= horizon;

export function legal(s) {
  const i = actor(s),
    j = other(i);
  const p = s[`p_${i}`],
    q = s[`p_${j}`];
  if (p === 'done') return ['WAIT'];
  const actions = new Set(['WAIT']);
  if (p === 'approach' && q === 'approach') {
    if (s[`c_${i}`]) actions.add('YIELD');
    if (!s[`r_${i}`]) actions.add('REQUEST');
  }
  if ((p === 'approach' && ['bay', 'done'].includes(q)) || (p === 'bay' && q === 'done')) {
    actions.add('PASS');
  }
  if (s[`r_${i}`]) actions.add('CANCEL');
  return ACTIONS.filter((a) => actions.has(a));
}

export function transition(s, action) {
  if (!legal(s).includes(action)) throw Error(`Illegal action: ${action}`);
  const i = actor(s),
    next = { ...s, t: s.t + 1 };
  if (action === 'PASS') next[`p_${i}`] = 'done';
  if (action === 'YIELD')
    Object.assign(next, {
      [`p_${i}`]: 'bay',
      first_yielder: i,
      r_A: 0,
      r_B: 0,
    });
  if (action === 'REQUEST' || action === 'CANCEL') next[`r_${i}`] = Number(action === 'REQUEST');
  return next;
}

export function demand(s, i, delta) {
  const j = other(i);
  if (!s[`c_${j}`]) return 0;
  if (!s[`c_${i}`]) return 1;
  return Number(s[`u_${i}`] - s[`u_${j}`] >= delta);
}

export function taskCost(s, action, i, parameters, config) {
  let cost = s[`p_${i}`] === 'done' ? 0 : s[`u_${i}`];
  if (actor(s) === i) {
    if (action === 'YIELD') cost += parameters.yield_cost;
    if (['REQUEST', 'CANCEL'].includes(action)) cost += config.communication_effort;
  }
  return cost;
}
