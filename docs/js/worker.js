/** Keep full-horizon computation off the UI thread. */
import { Session } from './session.js';
let session;
self.onmessage = async ({ data }) => {
  try {
    if (data.type === 'reset') {
      session = new Session(data.config, data.pair, data.condition, data.seed);
      self.postMessage({ type: 'reset', status: session.status() });
    } else if (data.type === 'episode') {
      self.postMessage({
        type: 'episode',
        result: await session.episode({
          training: data.training !== false,
          contextId: data.contextId || 0,
        }),
      });
    } else if (data.type === 'train') {
      while (session.status().blocks < data.target) {
        const result = await session.episode();
        if (result.after.completed % 12 === 0) {
          self.postMessage({ type: 'progress', status: result.after });
        }
      }
      self.postMessage({ type: 'trained', status: session.status() });
    }
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message });
  }
};
