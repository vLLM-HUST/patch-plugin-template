"""Entry point of a default-off, single-mechanism runtime-patch plugin.

This is a *template*. The example mechanism replaces a host method that scans a table once per
item with one that builds a lookup table once per call. Replace the four ``TODO`` constants and
``_make_replacement`` with your own mechanism; keep the structure, which encodes lessons from
real projects (see docs/PITFALLS.md):

* Import-safe and default-off: registration must not import any host module unless enabled.
* The kill switch always wins over the enable switch.
* A source guard refuses to patch a host that does not look like the one this was written for.
* Installation is idempotent.
* ``installed`` and ``runtime_effective`` are different facts and are reported separately, both
  carrying the pid of the process that produced them.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
from typing import Any

LOGGER = logging.getLogger(__name__)
PATCH_MARKER = "__example_plugin__"

# Environment variables are VLLM_HUST_<ENV>_ENABLE / _KILL_SWITCH / _EVIDENCE.
ENV = "EXAMPLE_PLUGIN"

# TODO: where the function you replace lives, and a token that is present in the *unoptimised*
# host source. If the token is missing the host is unsupported or already optimised.
HOST_MODULE = "example_host"
HOST_CLASS = "Worker"
HOST_METHOD = "compute"
EXPECTED_SOURCE_MARKER = "slow_lookup("


def _var(name: str) -> str:
    return f"VLLM_HUST_{ENV}_{name}"


def _enabled(name: str) -> bool:
    return os.getenv(_var(name), "0").strip().lower() in {"1", "true", "yes", "on"}


def _emit_evidence(message: str) -> None:
    """Print an audit event; goes to stderr because vLLM configures logging later in workers."""
    print(f"EVIDENCE {message} pid={os.getpid()}", file=sys.stderr, flush=True)


_runtime_effective_emitted = False


def _note_runtime_effective() -> None:
    """Emit one ``runtime_effective`` event per process, the first time the patched code runs.

    ``installed`` only says the class attribute was swapped. This says the replacement was
    actually *called*, and in which process.
    """
    global _runtime_effective_emitted
    if _runtime_effective_emitted or not _enabled("EVIDENCE"):
        return
    _runtime_effective_emitted = True
    _emit_evidence(f"runtime_effective mechanism={ENV.lower()}")


def _supported(host_cls: Any) -> None:
    """Refuse to patch an implementation that does not look like the one this was written for."""
    method = getattr(host_cls, HOST_METHOD, None)
    if method is None:
        raise RuntimeError(f"{ENV.lower()} cannot find {HOST_CLASS}.{HOST_METHOD}")
    if EXPECTED_SOURCE_MARKER not in inspect.getsource(method):
        raise RuntimeError(
            f"{ENV.lower()} cannot find the expected `{EXPECTED_SOURCE_MARKER}` in "
            f"{HOST_CLASS}.{HOST_METHOD}; this release is unsupported or already optimised"
        )


def _make_replacement() -> Any:
    """TODO: build your replacement. Keep the signature and the observable behaviour identical."""

    def compute(self, items):
        # Build the lookup once per call instead of scanning the table once per item.
        # The host returns the *first* match, so keep first-wins semantics.
        index: dict[Any, Any] = {}
        for key, value in self.table:
            index.setdefault(key, value)
        result = [index.get(item) for item in items]
        _note_runtime_effective()
        return result

    return compute


def _install(host_mod: Any) -> None:
    host_cls = getattr(host_mod, HOST_CLASS)
    if getattr(host_cls, PATCH_MARKER, False):
        return
    _supported(host_cls)
    setattr(host_cls, HOST_METHOD, _make_replacement())
    setattr(host_cls, PATCH_MARKER, True)
    LOGGER.info("%s installed on %s", ENV.lower(), host_cls.__name__)
    if _enabled("EVIDENCE"):
        _emit_evidence(f"installed mechanism={ENV.lower()} class={host_cls.__name__}")


def register() -> None:
    """Entry point called by vLLM in the API, engine-core and worker processes."""
    if _enabled("KILL_SWITCH"):
        LOGGER.warning("%s kill switch is active; not installed", ENV.lower())
        return
    if not _enabled("ENABLE"):
        LOGGER.info("%s is discovered but disabled", ENV.lower())
        return
    # Import the host only now, so a disabled plugin imports nothing from the runtime.
    _install(importlib.import_module(HOST_MODULE))
