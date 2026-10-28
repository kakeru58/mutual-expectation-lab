/** UI controls; the worker owns all learning and decisions. */
import { draw, emptyView, updateScenes, updateParameters } from './view.js';
import { t } from './i18n.js';
const $ = (id) => document.getElementById(id);
let config,
  worker,
  result,
  position = 0,
  timer,
  busy = true,
  status;
let notice = { source: 'Loading.', values: {} };
function notify(source, values = {}) {
  notice = { source, values };
  $('message').textContent = t(source, values);
}

function updateTraining() {
  if (!status) return;
  const remaining = Number($('target').value) * 12 - status.completed;
  $('train').disabled = busy || remaining <= 0;
  $('train').textContent =
    remaining > 0 ? t('Train {n} episodes', { n: remaining }) : t('Target reached');
  $('trainPlan').textContent =
    remaining > 0
      ? t('{n} episodes remaining to reach epoch {epoch}.', {
          n: remaining,
          epoch: $('target').value,
        })
      : t('Select a higher target epoch to continue training.');
}
function updateStatus(value) {
  status = value;
  $('blocks').textContent = value.blocks;
  $('experience').textContent = value.completed;
  $('epochProgress').value = value.completed % 12;
  $('epochProgressLabel').textContent = t('Current epoch: {n} of 12 episodes', {
    n: value.completed % 12,
  });
  $('memory').textContent = t('Observed partner actions: A {a}, B {b}.', {
    a: value.counts.A,
    b: value.counts.B,
  });
  updateTraining();
}
function setBusy(value) {
  busy = value;
  for (const id of ['run', 'evaluate', 'target']) $(id).disabled = value;
  updateTraining();
}
function clearEpisode() {
  clearInterval(timer);
  result = null;
  position = 0;
  emptyView();
}
function reset() {
  clearEpisode();
  if (worker) worker.terminate();
  $('target').value = '2';
  setBusy(true);
  const seed = Number($('seed').value);
  if (!Number.isInteger(seed) || seed < 0 || seed > 999999) {
    notify('Enter an integer seed between 0 and 999999.');
    return;
  }
  const pair = config.pairs.find((p) => p.id === Number($('pair').value));
  updateParameters(config);
  worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
  worker.onmessage = receive;
  worker.onerror = (event) => {
    notify('Execution error: {error}', { error: event.message });
    setBusy(true);
  };
  worker.postMessage({
    type: 'reset',
    config,
    pair: pair.id,
    condition: $('condition').value,
    seed,
  });
}
function render() {
  draw(result, position, config);
}
function receive({ data }) {
  if (data.type === 'error') {
    notify('{error}', { error: data.message });
    setBusy(false);
    return;
  }
  if (data.status) updateStatus(data.status);
  if (data.type === 'progress') {
    notify('Training progress: epoch {epoch}.', { epoch: data.status.blocks });
    return;
  }
  setBusy(false);
  if (data.type === 'reset') notify('No training data. Both prediction tables are empty.');
  if (data.type === 'trained')
    notify('Training complete: {epoch} epochs. Run an evaluation to inspect the current model.', {
      epoch: status.blocks,
    });
  if (data.type === 'episode') {
    result = data.result;
    position = 0;
    updateStatus(result.after);
    const trained = result.after.completed > result.before.completed;
    if (trained)
      notify('Training episode {n}. Started after {before} training episodes.', {
        n: result.after.completed,
        before: result.before.completed,
      });
    else
      notify('Evaluation after {n} training episodes. Training data unchanged.', {
        n: result.before.completed,
      });
    render();
    clearInterval(timer);
    timer = setInterval(() => {
      position++;
      render();
      if (position >= result.steps.length) clearInterval(timer);
    }, 850);
  }
}
function run(training) {
  if (busy) return;
  clearInterval(timer);
  setBusy(true);
  notify('Computing episode.');
  worker.postMessage({ type: 'episode', training, contextId: Number($('scene').value) });
}
$('run').onclick = () => run(true);
$('evaluate').onclick = () => run(false);
$('next').onclick = () => {
  clearInterval(timer);
  position++;
  render();
};
$('end').onclick = () => {
  clearInterval(timer);
  position = result.steps.length;
  render();
};
$('reset').onclick = () => config && reset();
for (const id of ['pair', 'condition', 'seed']) $(id).onchange = () => reset();
$('target').onchange = updateTraining;
$('train').onclick = () => {
  if (busy) return;
  const target = Number($('target').value);
  if (target * 12 <= status.completed) return;
  clearEpisode();
  setBusy(true);
  notify('Training to epoch {epoch}.', { epoch: target });
  worker.postMessage({ type: 'train', target });
};
document.addEventListener('languagechange', () => {
  updateScenes(config);
  updateParameters(config);
  if (status) updateStatus(status);
  if (result) render();
  else emptyView();
  notify(notice.source, notice.values);
});

try {
  const response = await fetch('./data/config.json');
  if (!response.ok) throw Error('Could not load configuration.');
  config = await response.json();
  updateScenes(config);
  reset();
} catch (error) {
  notify('{error} Open this page over HTTP or HTTPS.', { error: t(error.message) });
}
