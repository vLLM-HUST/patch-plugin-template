"""The plugin must refuse a host that does not look like the one it was written for."""

from __future__ import annotations

import types

import pytest

from example_plugin import plugin


def test_refuses_a_host_that_is_already_optimised(host):
    def compute(self, items):  # an already-optimised or different implementation
        return list(items)

    host.Worker.compute = compute
    with pytest.raises(RuntimeError, match="unsupported or already optimised"):
        plugin._install(host)
    assert not getattr(host.Worker, plugin.PATCH_MARKER, False)


def test_refuses_a_host_without_the_method(host):
    del host.Worker.compute
    with pytest.raises(RuntimeError, match="cannot find"):
        plugin._install(host)


def test_a_refused_install_leaves_the_host_untouched(host):
    host.Worker.compute = lambda self, items: items
    before = host.Worker.compute
    with pytest.raises(RuntimeError):
        plugin._install(types.SimpleNamespace(Worker=host.Worker))
    assert host.Worker.compute is before


def test_guard_is_a_substring_check_so_comments_can_satisfy_it(host):
    """Known limitation, pinned so nobody assumes more than it gives: the marker is matched against
    the whole source text, comments and strings included. Choose a distinctive *code* token."""

    def compute(self, items):  # slow_lookup( appears here only as a comment
        return list(items)

    host.Worker.compute = compute
    plugin._supported(host.Worker)  # does not raise
