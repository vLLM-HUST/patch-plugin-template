from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITHUB_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def test_mod_metadata_is_explicit_and_safe():
    metadata = json.loads((ROOT / "MOD_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["schema_version"] == "vllm-hust-mod-metadata-v1"
    assert metadata["canonical_repository"].startswith(
        f"https://github.com/vLLM-HUST/{metadata['repository']}"
    )

    responsibility = metadata["responsibility"]
    assert responsibility["organization"] == "vLLM-HUST"
    assert responsibility["maintainers"]
    advisor_status = responsibility["advisor_status"]
    advisors = responsibility["advisors"]
    assert isinstance(advisors, list)
    if metadata["mod_id"] == "example-plugin":
        assert responsibility["maintainers"] == [
            {"name": "EXAMPLE_MAINTAINER_NAME", "github": "EXAMPLE_MAINTAINER_GITHUB"}
        ]
        assert advisor_status == "EXAMPLE_ADVISOR_STATUS"
        assert advisors == []
        return

    for maintainer in responsibility["maintainers"]:
        assert maintainer["name"].strip()
        assert GITHUB_RE.fullmatch(maintainer["github"])

    assert advisor_status in {"none", "unknown", "declared"}
    if advisor_status in {"none", "unknown"}:
        assert advisors == []
    else:
        assert advisors
        for advisor in advisors:
            assert (
                {"name", "relationship"}
                <= set(advisor)
                <= {
                    "name",
                    "github",
                    "relationship",
                }
            )
            assert advisor["name"].strip()
            assert advisor["relationship"].strip()
            if "github" in advisor:
                assert GITHUB_RE.fullmatch(advisor["github"])

    assert metadata["lifecycle"]["default_enabled"] is False
    assert metadata["evidence"]["qualification"] in {
        "unqualified",
        "qualified",
        "not-beneficial-in-tested-cell",
        "rejected",
    }
    assert isinstance(metadata["evidence"]["performance_claims"], list)
