import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { JSDOM } from 'jsdom';
import { Session } from '../docs/js/session.js';

const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function until(condition) {
  for (let n = 0; n < 300; n++) {
    if (condition()) return;
    await pause(10);
  }
  throw Error('UI state did not arrive');
}

test('controls really reset to zero; natural REQUEST and CANCEL use speech bubbles', async () => {
  const html = await readFile(new URL('../docs/index.html', import.meta.url), 'utf8');
  const config = JSON.parse(
    await readFile(new URL('../expectation_lab/config.json', import.meta.url)),
  );
  const dom = new JSDOM(html, { url: 'https://example.test/project/' });
  globalThis.document = dom.window.document;
  if (!globalThis.crypto) globalThis.crypto = webcrypto;
  globalThis.fetch = async () => ({ ok: true, json: async () => config });
  const workers = [];
  globalThis.Worker = class {
    constructor() {
      workers.push(this);
      this.stopped = false;
    }
    terminate() {
      this.stopped = true;
    }
    postMessage(data) {
      queueMicrotask(async () => {
        const send = (message) => {
          if (!this.stopped) this.onmessage({ data: message });
        };
        try {
          if (data.type === 'reset') {
            this.session = new Session(data.config, data.pair, data.condition, data.seed);
            send({ type: 'reset', status: this.session.status() });
          } else if (data.type === 'episode') {
            send({
              type: 'episode',
              result: await this.session.episode({
                training: data.training !== false,
                contextId: data.contextId || 0,
              }),
            });
          } else if (data.type === 'train') {
            while (!this.stopped && this.session.status().blocks < data.target)
              await this.session.episode();
            send({ type: 'trained', status: this.session.status() });
          }
        } catch (error) {
          send({ type: 'error', message: error.message });
        }
      });
    }
  };
  const $ = (id) => document.getElementById(id);
  await import('../docs/js/app.js');
  await until(() => !$('run').disabled);
  assert.equal($('blocks').textContent, '0');
  assert.equal(workers.at(-1).session.status().completed, 0);
  assert.equal($('memory').textContent, 'Observed partner actions: A 0, B 0.');
  assert.equal($('experience').textContent, '0');
  assert.equal($('train').textContent, 'Train 24 episodes');
  $('run').click();
  await until(() => workers.at(-1).session.status().completed === 1 && !$('run').disabled);
  assert.match($('message').textContent, /Started after 0 training episodes/);
  assert.equal($('experience').textContent, '1');
  assert.equal($('epochProgress').value, 1);
  assert.equal($('train').textContent, 'Train 23 episodes');
  $('end').click();
  $('target').value = '2';
  $('train').click();
  await until(() => $('blocks').textContent === '2' && !$('run').disabled);
  assert.equal($('train').disabled, true);
  assert.equal($('experience').textContent, '24');
  const before = workers.at(-1).session.status();
  $('scene').value = '0';
  $('evaluate').click();
  await until(() => !$('evaluate').disabled);
  $('end').click();
  assert.deepEqual(workers.at(-1).session.status(), before);
  assert.ok(document.querySelector('.bubble'));
  assert.match($('conversation').textContent, /Please let me pass first/);
  const snapshot = structuredClone(workers.at(-1).session.status());
  const workerCount = workers.length;
  const turn = $('turn').textContent;
  const selectedScene = $('scene').value;
  const bubbleCount = document.querySelectorAll('.bubble').length;
  $('languageToggle').click();
  assert.equal(document.documentElement.lang, 'ja');
  assert.equal($('languageToggle').textContent, 'English');
  assert.match($('conversation').textContent, /先に通してほしいです/);
  assert.equal($('scene').value, selectedScene);
  assert.equal($('experience').textContent, '24');
  assert.equal(document.querySelectorAll('.bubble').length, bubbleCount);
  assert.deepEqual(workers.at(-1).session.status(), snapshot);
  assert.equal(workers.length, workerCount, 'language must not create a worker');
  assert.equal(document.defaultView.localStorage.getItem('expectation-lab-language'), 'ja');
  $('languageToggle').click();
  assert.equal(document.documentElement.lang, 'en');
  assert.equal($('turn').textContent, turn);
  assert.match($('conversation').textContent, /Please let me pass first/);
  assert.deepEqual(workers.at(-1).session.status(), snapshot);

  $('target').value = '5';
  $('target').dispatchEvent(new dom.window.Event('change'));
  assert.equal($('train').textContent, 'Train 36 episodes');
  $('train').click();
  await until(() => $('blocks').textContent === '5' && !$('run').disabled);
  $('evaluate').click();
  await until(() => !$('evaluate').disabled);
  $('end').click();
  assert.match($('conversation').textContent, /I withdraw my request/);
  for (const bubble of document.querySelectorAll('.bubble')) {
    assert.ok(['Please let me pass first.', 'I withdraw my request.'].includes(bubble.textContent));
  }
  $('reset').click();
  await until(() => !$('run').disabled);
  assert.deepEqual(workers.at(-1).session.status(), {
    completed: 0,
    blocks: 0,
    counts: { A: 0, B: 0 },
  });
  assert.match($('conversation').textContent, /No episode selected/);
  assert.equal(document.querySelectorAll('.bubble').length, 0);
  dom.window.close();
});
