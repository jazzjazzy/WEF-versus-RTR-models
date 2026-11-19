import hashlib
import json

from conftest import small_town


def fingerprint(*overrides):
    town = small_town("population_cap=80", "stop_on_failure=false", *overrides)
    town.run(4 * 52)
    blob = json.dumps(town.rec.events, sort_keys=True).encode()
    state = [(a.id, a.cash, a.klass, round(a.security, 9)) for a in town.agents]
    return hashlib.sha256(blob + json.dumps(state).encode()).hexdigest(), town


def test_same_seed_same_run():
    first, a = fingerprint("seed=11")
    second, b = fingerprint("seed=11")
    assert first == second
    assert a.rec.event_count == b.rec.event_count > 100


def test_different_seed_different_run():
    assert fingerprint("seed=11")[0] != fingerprint("seed=12")[0]
