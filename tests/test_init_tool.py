"""The init tool must leave a repository that has no placeholder left and still passes its tests."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ("example_plugin", "example-plugin", "EXAMPLE_PLUGIN")


def copy_repo(dst: Path) -> None:
    ignore = shutil.ignore_patterns(
        ".git", ".pytest_cache", ".ruff_cache", "__pycache__", ".venv", "dist", "build"
    )
    shutil.copytree(ROOT, dst, ignore=ignore)


def test_init_leaves_no_placeholder_and_the_result_passes(tmp_path):
    work = tmp_path / "demo"
    copy_repo(work)
    out = subprocess.run(
        [sys.executable, "tools/init_plugin.py", "--name", "demo-plugin"],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    assert (work / "src" / "demo_plugin" / "plugin.py").exists()
    assert not (work / "src" / "example_plugin").exists()
    assert not (work / "tools").exists()

    for path in work.rglob("*"):
        if path.is_file() and path.name != "LICENSE" and "__pycache__" not in path.parts:
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert not any(token in text for token in TOKENS), f"placeholder left in {path.relative_to(work)}"

    manifest = (work / "src" / "demo_plugin" / "manifests" / "vllm-hust-extension-v0.2.json").read_text()
    assert "org.vllm-hust.demo-plugin" in manifest

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_dry_run_changes_nothing(tmp_path):
    work = tmp_path / "demo"
    copy_repo(work)
    before = (work / "pyproject.toml").read_text()
    out = subprocess.run(
        [sys.executable, "tools/init_plugin.py", "--name", "demo-plugin", "--dry-run"],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0
    assert (work / "pyproject.toml").read_text() == before
    assert (work / "src" / "example_plugin").exists()


def test_rejects_bad_names(tmp_path):
    work = tmp_path / "demo"
    copy_repo(work)
    for bad in ("Bad_Name", "-x", "example-plugin"):
        out = subprocess.run(
            [sys.executable, "tools/init_plugin.py", "--name", bad],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        assert out.returncode != 0
