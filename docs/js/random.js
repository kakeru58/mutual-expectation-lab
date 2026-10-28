/** SHA256-keyed CPython integer seeding + MT19937. See THIRD_PARTY.md. */
class PythonRandom {
  constructor(words) {
    const mt = (this.state = new Uint32Array(624));
    mt[0] = 19650218;
    for (let i = 1; i < 624; i++) {
      mt[i] = (Math.imul(1812433253, mt[i - 1] ^ (mt[i - 1] >>> 30)) + i) >>> 0;
    }
    let i = 1,
      j = 0;
    for (let k = Math.max(624, words.length); k > 0; k--) {
      mt[i] = ((mt[i] ^ Math.imul(mt[i - 1] ^ (mt[i - 1] >>> 30), 1664525)) + words[j] + j) >>> 0;
      if (++i >= 624) {
        mt[0] = mt[623];
        i = 1;
      }
      if (++j >= words.length) j = 0;
    }
    for (let k = 623; k > 0; k--) {
      mt[i] = ((mt[i] ^ Math.imul(mt[i - 1] ^ (mt[i - 1] >>> 30), 1566083941)) - i) >>> 0;
      if (++i >= 624) {
        mt[0] = mt[623];
        i = 1;
      }
    }
    mt[0] = 0x80000000;
    this.index = 624;
  }
  uint32() {
    const mt = this.state;
    if (this.index >= 624) {
      for (let i = 0; i < 624; i++) {
        const y = (mt[i] & 0x80000000) | (mt[(i + 1) % 624] & 0x7fffffff);
        mt[i] = mt[(i + 397) % 624] ^ (y >>> 1) ^ (y & 1 ? 0x9908b0df : 0);
      }
      this.index = 0;
    }
    let y = mt[this.index++];
    y ^= y >>> 11;
    y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000;
    y ^= y >>> 18;
    return y >>> 0;
  }
  random() {
    return ((this.uint32() >>> 5) * 67108864 + (this.uint32() >>> 6)) / 9007199254740992;
  }
  below(n) {
    const bits = Math.floor(Math.log2(n)) + 1;
    let r;
    do {
      r = this.uint32() >>> (32 - bits);
    } while (r >= n);
    return r;
  }
  choice(values) {
    return values[this.below(values.length)];
  }
  shuffle(values) {
    for (let i = values.length - 1; i > 0; i--) {
      const j = this.below(i + 1);
      [values[i], values[j]] = [values[j], values[i]];
    }
    return values;
  }
}

export async function keyed(...key) {
  const bytes = new TextEncoder().encode(JSON.stringify(key));
  const digest = new DataView(await crypto.subtle.digest('SHA-256', bytes));
  const words = [];
  for (let offset = 28; offset >= 0; offset -= 4) words.push(digest.getUint32(offset));
  while (words.length > 1 && words.at(-1) === 0) words.pop();
  return new PythonRandom(words);
}
