"""The pyproject parameters depend on each other; these tests pin the relationships that broke or
could silently drift: build-backend floor, version source, packaging scope, Python range."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cfg():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest():
    path = next((ROOT / "src").glob("*/manifests/vllm-hust-extension-v0.3.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def test_setuptools_floor_supports_an_spdx_license_string(cfg):
    # `license = "Apache-2.0"` (a string, not a table) needs setuptools >= 77: 76.1.0 fails to
    # build the metadata, 77.0.3 builds it. The floor in [build-system] must not be lower.
    assert isinstance(cfg["project"]["license"], str)
    (spec,) = [Requirement(r) for r in cfg["build-system"]["requires"] if r.startswith("setuptools")]
    assert not spec.specifier.contains("76.1.0")
    assert spec.specifier.contains("77.0.3")


def test_the_version_comes_from_one_place_and_the_manifest_agrees(cfg, manifest):
    assert "version" in cfg["project"]["dynamic"]
    module, _, attr = cfg["tool"]["setuptools"]["dynamic"]["version"]["attr"].rpartition(".")
    version = getattr(importlib.import_module(module), attr)
    assert manifest["extension_version"] == version, "bump _version.py and the manifest together"


def test_packaging_scope_covers_the_plugin_and_its_manifest(cfg):
    find = cfg["tool"]["setuptools"]["packages"]["find"]
    src = ROOT / find["where"][0]
    assert src.is_dir()
    packages = [p.name for p in src.iterdir() if (p / "__init__.py").exists()]
    assert packages, "no importable package under the src directory"
    package_data = cfg["tool"]["setuptools"]["package-data"]
    for package in packages:
        # The JSON is not Python, so without package-data it is left out of the wheel and the
        # manager cannot find the manifest.
        assert "manifests/*.json" in package_data[package]
        assert list((src / package / "manifests").glob("*.json"))


def test_python_range_is_consistent(cfg):
    minimum = re.search(r">=\s*(\d+)\.(\d+)", cfg["project"]["requires-python"])
    major, minor = int(minimum.group(1)), int(minimum.group(2))
    assert cfg["tool"]["ruff"]["target-version"] == f"py{major}{minor}"
    classifiers = cfg["project"]["classifiers"]
    assert f"Programming Language :: Python :: {major}.{minor}" in classifiers
    advertised = [
        (int(m.group(1)), int(m.group(2)))
        for c in classifiers
        if (m := re.fullmatch(r"Programming Language :: Python :: (\d+)\.(\d+)", c))
    ]
    assert advertised, "no per-version Python classifiers"
    assert min(advertised) == (major, minor), "classifiers must start at requires-python"


def test_the_test_extra_covers_what_the_suite_imports(cfg):
    extra = " ".join(cfg["project"]["optional-dependencies"]["test"])
    assert "pytest" in extra and "ruff" in extra
    assert "tomli" in extra  # tomllib is missing on Python 3.10
