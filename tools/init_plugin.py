#!/usr/bin/env python3
"""Rename the template's placeholders in place.

GitHub templates copy files but do not substitute variables. After "Use this template", run::

    python tools/init_plugin.py --name my-plugin

It rewrites ``example-plugin`` / ``example_plugin`` / ``EXAMPLE_PLUGIN`` everywhere, renames the
package directory, and removes this tool and its test (use ``--keep-tool`` to keep them).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".pytest_cache", ".ruff_cache", "__pycache__", ".venv", "dist", "build"}
SKIP_FILES = {"tools/init_plugin.py", "tests/test_init_tool.py", "LICENSE"}
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in SKIP_FILES:
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--name", required=True, help="distribution name, lowercase with dashes, e.g. my-plugin"
    )
    parser.add_argument("--extension-id", help="default: org.vllm-hust.<name>")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this repo)")
    parser.add_argument("--keep-tool", action="store_true", help="keep tools/init_plugin.py and its test")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not NAME_RE.match(args.name):
        parser.error("--name must be lowercase letters/digits separated by single dashes")
    if args.name == "example-plugin":
        parser.error("choose a name other than the template's own")

    module = args.name.replace("-", "_")
    env = module.upper()
    root = args.root.resolve()
    changed = []
    for path in text_files(root):
        old = path.read_text(encoding="utf-8")
        new = old
        if args.extension_id:
            new = new.replace("org.vllm-hust.example-plugin", args.extension_id)
        new = (
            new.replace("example-plugin", args.name)
            .replace("example_plugin", module)
            .replace("EXAMPLE_PLUGIN", env)
        )
        if new != old:
            changed.append(path.relative_to(root).as_posix())
            if not args.dry_run:
                path.write_text(new, encoding="utf-8")

    package_dir = root / "src" / "example_plugin"
    if package_dir.exists():
        changed.append("src/example_plugin -> src/" + module)
        if not args.dry_run:
            package_dir.rename(root / "src" / module)

    if not args.keep_tool and not args.dry_run:
        (root / "tests" / "test_init_tool.py").unlink(missing_ok=True)
        shutil.rmtree(root / "tools", ignore_errors=True)

    print(f"{'would update' if args.dry_run else 'updated'} {len(changed)} item(s):")
    for item in changed:
        print("  " + item)
    print(
        f"module={module} env_prefix=VLLM_HUST_{env}_* extension_id={args.extension_id or 'org.vllm-hust.' + args.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
