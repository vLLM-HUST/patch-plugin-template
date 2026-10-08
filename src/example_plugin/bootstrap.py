"""Make the patch reach a process the host starts with ``multiprocessing`` *spawn*.

vLLM loads general plugins in its own processes. A side process started by the host with the
spawn method (an EPLB planner, a metrics worker, ...) is a fresh interpreter that never runs
plugin loading, so patching a class in the parent does not change what the child executes. Symptom:
``installed`` is reported, ``runtime_effective`` never is, and the original code keeps running.

Fix: replace the host's launcher so the child starts at ``child_entry``, a module-level function
(pickled by reference), which registers the plugin and then runs the host's own target::

    def _launch_process(self):
        proc = Process(target=child_entry, args=(self.worker_process, self.q1, self.q2), daemon=True)
        proc.start()
        return proc

Guard the launcher replacement with the same source check as any other patch.
"""

from __future__ import annotations

from typing import Any


def child_entry(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Install the plugin in this fresh interpreter, then run the host's original target."""
    from .plugin import register

    register()
    return target(*args, **kwargs)
