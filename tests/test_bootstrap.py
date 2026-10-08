from __future__ import annotations

import pickle

from example_plugin import bootstrap, plugin


def test_child_entry_pickles_by_reference_for_spawn():
    # spawn pickles the Process target; a closure or a bound method of a patched class would fail.
    assert pickle.loads(pickle.dumps(bootstrap.child_entry)) is bootstrap.child_entry


def test_child_entry_registers_then_runs_the_host_target(monkeypatch):
    calls = []
    monkeypatch.setattr(plugin, "register", lambda: calls.append("register"))
    result = bootstrap.child_entry(lambda a, b=0: calls.append(("target", a, b)) or "done", 1, b=2)
    assert calls == ["register", ("target", 1, 2)]
    assert result == "done"
