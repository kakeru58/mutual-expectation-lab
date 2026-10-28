import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { Session } from '../docs/js/session.js';
import { keyed } from '../docs/js/random.js';
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const config = JSON.parse(
  await readFile(new URL('../expectation_lab/config.json', import.meta.url)),
);
const fixture = JSON.parse(await readFile(new URL('./browser-fixtures.json', import.meta.url)));
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test('SHA256 + integer MT seeding, random, choice and shuffle match CPython', async () => {
  for (const entry of fixture.random) {
    const rng = await keyed(...entry.key);
    assert.deepEqual(rng.shuffle(Array.from({ length: 12 }, (_, i) => i)), entry.shuffle);
    close((await keyed(...entry.draw_key)).random(), entry.draw);
    assert.equal(
      (await keyed(...entry.draw_key)).choice(['YIELD', 'WAIT', 'REQUEST']),
      entry.choice,
    );
  }
});

test('browser starts at zero, learns independently, and matches 360 reference episodes', async () => {
  for (const entry of fixture.cases) {
    const session = new Session(config, entry.pair, entry.condition, 0);
    assert.deepEqual(session.status(), { completed: 0, blocks: 0, counts: { A: 0, B: 0 } });
    assert.equal(session.agents.A.planner.config.pairs, undefined);
    assert.equal(session.agents.A.planner.config.conditions, undefined);
    for (const stage of [0, 2]) {
      if (stage === 2) for (let i = 0; i < 24; i++) await session.episode();
      const before = session.status();
      if (stage === 2) assert.deepEqual(before.counts, entry.observations_after_2);
      for (let cid = 0; cid < 12; cid++) {
        const actual = await session.episode({ training: false, contextId: cid });
        const expected = entry.stages[String(stage)][cid];
        assert.equal(actual.steps.length, expected.length);
        for (const [n, row] of actual.steps.entries()) {
          const ref = expected[n];
          for (const field of ['actor', 'selected', 'executed', 'state_after'])
            assert.deepEqual(row[field], ref[field]);
          for (const i of ['A', 'B']) {
            close(row.task_increment[i], ref.task_increment[i]);
            close(row.expectation_increment[i], ref.expectation_increment[i]);
          }
          for (const [action, [task, loss]] of Object.entries(row.candidates)) {
            const enabled = config.conditions.find((c) => c.id === entry.condition)[
              'g_' + row.actor
            ];
            const weight = config.pairs.find((p) => p.id === entry.pair)[row.actor]
              .expectation_weight;
            close(task, ref.candidates[action].task_cost);
            close(task + enabled * weight * loss, ref.candidates[action].total);
          }
        }
      }
      assert.deepEqual(session.status(), before, 'frozen observation must not learn');
    }
    const reset = new Session(config, entry.pair, entry.condition, 0);
    assert.equal(reset.status().completed, 0);
    assert.deepEqual(reset.status().counts, { A: 0, B: 0 });
  }
});
