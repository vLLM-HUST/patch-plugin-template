"""A stand-in for the real host, so the template's tests run without vLLM installed.

Mirror the *shape* of the code you patch: the unoptimised host method, and any module-level helper
it calls. The differential tests compare the replacement against this original.
"""

from __future__ import annotations

import types


def make() -> types.ModuleType:
    module = types.ModuleType("example_host")

    def slow_lookup(table, key):
        for candidate, value in table:
            if candidate == key:
                return value
        return None

    class Worker:
        def __init__(self, table):
            self.table = table

        def compute(self, items):
            result = []
            for item in items:
                result.append(slow_lookup(self.table, item))
            return result

    module.slow_lookup = slow_lookup
    module.Worker = Worker
    return module
