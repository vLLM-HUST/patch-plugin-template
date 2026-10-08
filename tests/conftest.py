from __future__ import annotations

import sys

import fake_host
import pytest

from example_plugin import plugin


@pytest.fixture
def host(monkeypatch):
    """A fresh fake host module registered as ``example_host``, with plugin state reset."""
    module = fake_host.make()
    monkeypatch.setitem(sys.modules, plugin.HOST_MODULE, module)
    monkeypatch.setattr(plugin, "_runtime_effective_emitted", False)
    for name in ("ENABLE", "KILL_SWITCH", "EVIDENCE"):
        monkeypatch.delenv(plugin._var(name), raising=False)
    return module
