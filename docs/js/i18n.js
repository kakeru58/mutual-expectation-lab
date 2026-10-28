/** Display-only localization. Never reads or writes experiment state. */
import experiment from './locales/experiment.js';
import messages from './locales/messages.js';
import reference from './locales/reference.js';
const ja = { ...experiment, ...messages, ...reference };
const STORAGE_KEY = 'expectation-lab-language';
let language = 'en';

export function t(source, values = {}) {
  const text = language === 'ja' ? (ja[source] ?? source) : source;
  return text.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? `{${key}}`));
}

export function initializeLanguage(page = document) {
  const button = page.getElementById('languageToggle');
  const texts = [],
    attributes = [],
    title = page.title;
  const walker = page.createTreeWalker(page.body, 4);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (node.parentElement.closest('script, style, code, #languageToggle')) continue;
    const source = node.textContent.trim().replace(/\s+/g, ' ');
    if (ja[source]) texts.push({ node, raw: node.textContent, source });
  }
  for (const element of page.querySelectorAll('[aria-label], [alt], [title]')) {
    for (const name of ['aria-label', 'alt', 'title']) {
      const value = element.getAttribute(name);
      if (value && ja[value]) attributes.push({ element, name, value });
    }
  }
  function apply() {
    page.documentElement.lang = language;
    page.title = t(title);
    for (const { node, raw, source } of texts) {
      if (node.isConnected) node.textContent = language === 'en' ? raw : t(source);
    }
    for (const { element, name, value } of attributes) element.setAttribute(name, t(value));
    button.textContent = language === 'en' ? '日本語' : 'English';
    button.setAttribute(
      'aria-label',
      language === 'en' ? 'Switch to Japanese' : '英語に切り替える',
    );
  }
  try {
    language = page.defaultView.localStorage.getItem(STORAGE_KEY) === 'ja' ? 'ja' : 'en';
  } catch {
    /* Storage is optional. */
  }
  button.onclick = () => {
    language = language === 'en' ? 'ja' : 'en';
    try {
      page.defaultView.localStorage.setItem(STORAGE_KEY, language);
    } catch {
      /* Keep switching available. */
    }
    apply();
    page.dispatchEvent(new page.defaultView.Event('languagechange'));
  };
  apply();
}

if (typeof document !== 'undefined') initializeLanguage();
