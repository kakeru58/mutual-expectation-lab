/** Display recorded actions; no decisions or learning happen here. */
import { t } from './i18n.js';
const $ = (id) => document.getElementById(id);
const labels = {
  WAIT: 'Wait',
  YIELD: 'Yield',
  PASS: 'Pass',
  REQUEST: 'Request',
  CANCEL: 'Cancel',
};
const say = { REQUEST: 'Please let me pass first.', CANCEL: 'I withdraw my request.' };
const actions = {
  WAIT: 'Waits.',
  YIELD: 'Moves into the bay.',
  PASS: 'Passes through the corridor.',
};
export const node = (tag, text, cls) => {
  const element = document.createElement(tag);
  element.textContent = text;
  if (cls) element.className = cls;
  return element;
};
export function move(state) {
  const positions = {
    A: { approach: [220, 138], bay: [302, 204], done: [670, 138] },
    B: { approach: [540, 138], bay: [457, 62], done: [90, 138] },
  };
  for (const i of ['A', 'B'])
    $('avatar' + i).setAttribute(
      'transform',
      `translate(${positions[i][state['p_' + i]].join(',')})`,
    );
}
export function draw(result, position, config) {
  if (!result) return;
  const row = result.steps[Math.max(0, position - 1)];
  const state = position === 0 ? row.state_before : row.state_after;
  move(state);
  $('sceneTitle').textContent = t('Urgency: A {a}, B {b}', { a: state.u_A, b: state.u_B });
  $('turn').textContent =
    position === 0 ? t('Before step 1') : t('After step {n}', { n: position });
  $('people').replaceChildren(
    ...['A', 'B'].map((i) => {
      const p = node('p', '');
      p.append(
        node('b', i),
        document.createTextNode(t(state['c_' + i] ? 'Can yield' : 'Cannot yield')),
      );
      return p;
    }),
  );
  const conversation = $('conversation');
  conversation.replaceChildren();
  const past = result.steps.slice(0, position);
  if (!past.length) conversation.append(node('p', t('No actions yet.'), 'empty'));
  for (const r of past) {
    const event = node('div', '', 'event ' + r.actor.toLowerCase());
    event.append(node('small', t('{id}, step {n}', { id: r.actor, n: r.state_before.t + 1 })));
    event.append(
      node(
        'div',
        t(
          say[r.executed] ||
            (r.automatic_wait ? 'Already arrived. Skips turn.' : actions[r.executed]),
        ),
        say[r.executed] ? 'bubble' : 'action',
      ),
    );
    if (r.exploration) event.append(node('small', t(' Exploration action')));
    conversation.append(event);
  }
  const last = past.at(-1);
  if (last?.termination)
    conversation.append(
      node(
        'p',
        t(last.termination === 'success' ? 'Both agents arrived.' : 'Time limit reached.'),
        'terminal',
      ),
    );
  conversation.scrollTop = conversation.scrollHeight;
  const messages = past.filter((r) => say[r.executed]).length;
  $('speechCount').textContent = t(messages === 1 ? '{n} message' : '{n} messages', {
    n: messages,
  });
  $('thoughts').replaceChildren(
    ...['A', 'B'].map((i) => {
      const enabled = config.conditions.find((c) => c.id === $('condition').value)['g_' + i];
      const text = !enabled
        ? 'Expectation cost disabled'
        : row.state_before.first_yielder !== null
          ? 'Priority settled'
          : row.d[i]
            ? 'Demands that the partner yield first'
            : 'No demand in this scenario';
      return node(
        'p',
        t('{id}: {text}. Internal state before this action, not a message.', {
          id: i,
          text: t(text),
        }),
      );
    }),
  );
  $('decision').textContent = t('{id}: planned {planned}, executed {executed}.', {
    id: row.actor,
    planned: t(labels[row.selected]),
    executed: t(labels[row.executed]),
  });
  $('candidates').replaceChildren();
  const parameters = config.pairs.find((p) => p.id === Number($('pair').value))[row.actor];
  const enabled = config.conditions.find((c) => c.id === $('condition').value)['g_' + row.actor];
  for (const [action, [task, loss]] of Object.entries(row.candidates)) {
    const cost = enabled * parameters.expectation_weight * loss;
    const tr = node('tr', '', action === row.selected ? 'chosen' : '');
    for (const value of [
      t(labels[action]),
      task.toFixed(3),
      cost.toFixed(3),
      (task + cost).toFixed(3),
    ])
      tr.append(node('td', value));
    $('candidates').append(tr);
  }
  $('forecast').textContent =
    t("{observer}'s prediction of {actor} before the action: ", {
      observer: row.observer,
      actor: row.actor,
    }) +
    Object.entries(row.q)
      .map(([a, p]) => `${t(labels[a])} ${(100 * p).toFixed(0)}%`)
      .join(', ');
  $('next').disabled = position >= result.steps.length;
  $('end').disabled = position >= result.steps.length;
}

export function emptyView() {
  $('conversation').replaceChildren(node('p', t('No episode selected.'), 'empty'));
  for (const id of ['candidates', 'thoughts']) $(id).replaceChildren();
  $('decision').textContent = '';
  $('forecast').textContent = '';
  $('next').disabled = true;
  $('end').disabled = true;
  $('sceneTitle').textContent = t('No episode selected');
  $('turn').textContent = t('Not started');
  $('speechCount').textContent = t('{n} messages', { n: 0 });
  move({ p_A: 'approach', p_B: 'approach' });
  $('people').replaceChildren(node('p', 'A'), node('p', 'B'));
}

export function updateScenes(config) {
  if (!config) return;
  const selected = $('scene').value;
  $('scene').replaceChildren();
  let cid = 0;
  for (const a of config.urgencies)
    for (const b of config.urgencies) {
      for (const [ca, cb] of config.capability_patterns) {
        const option = node(
          'option',
          t('Urgency A={a}, B={b}; can yield: {ability}', {
            a,
            b,
            ability: t(ca && cb ? 'both' : ca ? 'A only' : 'B only'),
          }),
        );
        option.value = cid++;
        $('scene').append(option);
      }
    }
  if (selected !== '') $('scene').value = selected;
}
export function updateParameters(config) {
  if (!config) return;
  const pair = config.pairs.find((p) => p.id === Number($('pair').value));
  $('parameters').textContent = ['A', 'B']
    .map((i) =>
      t('{id}: yielding cost {k}, delta {delta}, weight {w}', {
        id: i,
        k: pair[i].yield_cost,
        delta: pair[i].delta,
        w: pair[i].expectation_weight,
      }),
    )
    .join('; ');
}
