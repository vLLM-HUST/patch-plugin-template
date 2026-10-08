from __future__ import annotations

import importlib

from example_plugin import plugin


def _forbid_host_import(monkeypatch):
    def forbidden(name, *args, **kwargs):
        raise AssertionError(f"registration imported {name}")

    monkeypatch.setattr(importlib, "import_module", forbidden)


def test_discovery_is_a_noop_without_enable(host, monkeypatch):
    _forbid_host_import(monkeypatch)
    plugin.register()
    assert not getattr(host.Worker, plugin.PATCH_MARKER, False)


def test_kill_switch_wins_over_enable(host, monkeypatch):
    monkeypatch.setenv(plugin._var("ENABLE"), "1")
    monkeypatch.setenv(plugin._var("KILL_SWITCH"), "1")
    _forbid_host_import(monkeypatch)
    plugin.register()
    assert not getattr(host.Worker, plugin.PATCH_MARKER, False)


def test_enable_installs_and_is_idempotent(host, monkeypatch):
    monkeypatch.setenv(plugin._var("ENABLE"), "1")
    original = host.Worker.compute
    plugin.register()
    patched = host.Worker.compute
    assert patched is not original
    plugin.register()
    assert host.Worker.compute is patched
