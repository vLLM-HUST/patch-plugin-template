"""Differential tests: the replacement must behave exactly like the original host method.

This is the strongest evidence a runtime patch can offer. Do not only test a few hand-picked
cases: generate many random inputs, including the awkward ones (duplicates, misses, empty).
"""

from __future__ import annotations

import random

import fake_host
import pytest

from example_plugin import plugin


def random_case(seed: int):
    rng = random.Random(seed)
    keys = list(range(rng.choice([0, 1, 5, 40])))
    table = (
        [(rng.choice(keys), rng.randrange(1000)) for _ in range(rng.choice([0, 1, 30, 200]))] if keys else []
    )
    items = [rng.choice(keys + [-1, 999]) for _ in range(rng.choice([0, 1, 50]))]
    return table, items


@pytest.mark.parametrize("seed", range(100))
def test_replacement_matches_original(host, seed):
    table, items = random_case(seed)
    reference = fake_host.make().Worker(table).compute(items)  # untouched copy of the original
    plugin._install(host)
    patched = host.Worker(table).compute(items)
    assert patched == reference


def test_first_match_wins_like_the_host(host):
    plugin._install(host)
    assert host.Worker([("a", 1), ("a", 2)]).compute(["a"]) == [1]


def test_runtime_effective_is_reported_once_per_process(host, monkeypatch, capsys):
    monkeypatch.setenv(plugin._var("EVIDENCE"), "1")
    plugin._install(host)
    worker = host.Worker([(1, 10)])
    worker.compute([1])
    worker.compute([1])
    err = capsys.readouterr().err
    assert err.count("runtime_effective") == 1
    assert err.count("installed mechanism") == 1
    assert "pid=" in err
