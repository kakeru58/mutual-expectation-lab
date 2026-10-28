import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM } from 'jsdom';

test('all pages switch languages; the saved preference changes no numeric results', async () => {
  for (const [page, heading] of [
    ['index', '実験'],
    ['results', '参照結果'],
    ['model', 'モデル'],
  ]) {
    const html = await readFile(new URL(`../docs/${page}.html`, import.meta.url), 'utf8');
    const dom = new JSDOM(html, { url: `https://example.test/project/${page}.html` });
    globalThis.document = dom.window.document;
    const { initializeLanguage } = await import('../docs/js/i18n.js');
    const numericCells = () =>
      [...document.querySelectorAll('td')]
        .map((cell) => cell.textContent.trim())
        .filter((text) => /^\d+(\.\d+)?$/.test(text));
    const numbers = numericCells();
    const links = [...document.querySelectorAll('a')].map((link) => link.href);
    dom.window.localStorage.setItem('expectation-lab-language', 'ja');
    initializeLanguage();
    assert.equal(document.documentElement.lang, 'ja');
    assert.equal(document.querySelector('h1').textContent, heading);
    assert.equal(document.getElementById('languageToggle').textContent, 'English');
    assert.deepEqual(numericCells(), numbers);
    assert.deepEqual(
      [...document.querySelectorAll('a')].map((link) => link.href),
      links,
    );
    document.getElementById('languageToggle').click();
    assert.equal(document.documentElement.lang, 'en');
    assert.equal(dom.window.localStorage.getItem('expectation-lab-language'), 'en');
    assert.equal(
      document.querySelector('h1').textContent,
      { index: 'Experiment', results: 'Reference results', model: 'Model' }[page],
    );
    dom.window.close();
  }
});
