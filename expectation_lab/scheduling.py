"""Condition-independent SHA256 keys and balanced scene ordering."""

import hashlib
import itertools
import json
import random


def keyed(*key):
    raw = json.dumps(key, ensure_ascii=False, separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def contexts(config):
    return list(
        itertools.product(
            config["urgencies"], config["urgencies"], config["capability_patterns"]
        )
    )


def schedule(config, pair_id, seed, blocks):
    rows = []
    for block in range(blocks):
        order = list(range(len(contexts(config))))
        keyed(pair_id, seed, block, "context_order").shuffle(order)
        rows.extend((block, slot, context_id) for slot, context_id in enumerate(order))
    return rows
