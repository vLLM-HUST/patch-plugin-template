"""The manifest, pyproject and plugin constants describe one extension; keep them consistent.

These are the mismatches that silently break discovery or hide a conflict: an entry point that
differs from the manifest, an extension id that differs between the two, or a resource claim that
names a different function from the one the plugin actually replaces.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from example_plugin import plugin

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = next((ROOT / "src").glob("*/manifests/vllm-hust-extension-v0.3.json"))
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
RESOURCE = re.compile(r"^[a-z0-9][a-z0-9._:/-]*$")


@pytest.fixture(scope="module")
def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def pyproject():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_schema_version_and_filename_are_0_3(manifest):
    assert manifest["schema_version"] == "0.3-experimental"
    assert MANIFEST.name == "vllm-hust-extension-v0.3.json"  # the manager looks for this name first


def test_0_3_only_fields_are_present_and_well_formed(manifest):
    # `resource_claims` / `requires_extensions` are only legal under 0.3-experimental.
    assert manifest["requires_extensions"] == []
    claims = manifest["resource_claims"]
    assert claims, "declare what this plugin replaces so a competing plugin is rejected before launch"
    for claim in claims:
        assert set(claim) == {"resource", "scope", "mode"}
        assert RESOURCE.fullmatch(claim["resource"])
        assert IDENTIFIER.fullmatch(claim["scope"])
        assert claim["mode"] in {"exclusive", "shared"}
    assert len({(c["resource"], c["scope"]) for c in claims}) == len(claims)


def test_the_claimed_resource_is_the_function_the_plugin_replaces(manifest):
    expected = f"{plugin.HOST_MODULE.replace('_', '-')}.{plugin.HOST_CLASS.lower()}.{plugin.HOST_METHOD}"
    assert expected in {c["resource"] for c in manifest["resource_claims"]}
    # Replacing a function is exclusive: two plugins cannot both own it.
    patched = [c for c in manifest["resource_claims"] if c["resource"] == expected]
    assert all(c["mode"] == "exclusive" for c in patched)


def test_extension_id_and_entry_points_agree_with_pyproject(manifest, pyproject):
    assert IDENTIFIER.fullmatch(manifest["extension_id"])
    bundles = pyproject["project"]["entry-points"]["vllm_hust.extension_bundles"]
    assert manifest["extension_id"] in bundles

    declared = {(e["group"], e["name"]) for e in manifest["activation"]["entry_points"]}
    plugins = pyproject["project"]["entry-points"]["vllm.general_plugins"]
    assert declared == {("vllm.general_plugins", name) for name in plugins}


def test_implementation_points_at_register(manifest):
    impl = manifest["implementation"][0]
    assert (impl["module"], impl["object"]) == (plugin.__name__, "register")


def test_activation_environment_names_match_the_plugin(manifest):
    env = manifest["activation"]["environment"]
    assert set(env) == {plugin._var(name) for name in ("ENABLE", "KILL_SWITCH", "EVIDENCE")}
    assert env[plugin._var("ENABLE")] == "0"  # default off


def test_the_real_manager_accepts_it_when_installed(manifest):
    """Strongest check, skipped where vllm-hust-ext is not installed (it is not a dependency)."""
    parse = pytest.importorskip("vllm_hust_ext.manifest").parse_manifest
    parsed = parse(manifest)
    assert parsed.schema_version == "0.3-experimental"
    assert parsed.resource_claims
