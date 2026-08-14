import json
from pathlib import Path

import pytest

from tools.validate_contract import validate_document


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_example_matches_schema() -> None:
    errors = validate_document(
        ROOT / "examples" / "manifest.example.json",
        ROOT / "schemas" / "manifest.schema.json",
    )
    assert errors == []


def test_manifest_rejects_short_commit(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "examples" / "manifest.example.json").read_text("utf-8"))
    payload["git_commit"] = "abc1234"
    candidate = tmp_path / "manifest.json"
    candidate.write_text(json.dumps(payload), encoding="utf-8")
    errors = validate_document(candidate, ROOT / "schemas" / "manifest.schema.json")
    assert any("git_commit" in error for error in errors)


@pytest.mark.parametrize(
    ("document", "schema"),
    [
        ("metrics.example.json", "metrics.schema.json"),
        ("expected_metrics.example.json", "expected_metrics.schema.json"),
    ],
)
def test_metric_examples_match_schemas(document: str, schema: str) -> None:
    assert validate_document(ROOT / "examples" / document, ROOT / "schemas" / schema) == []


def test_metrics_allows_negative_transfer_conclusion(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "examples" / "metrics.example.json").read_text("utf-8"))
    payload["conclusion"] = "NO_POSITIVE_TRANSFER_SUPPORTED"
    candidate = tmp_path / "metrics.json"
    candidate.write_text(json.dumps(payload), encoding="utf-8")
    assert validate_document(candidate, ROOT / "schemas" / "metrics.schema.json") == []


def test_manifest_accepts_v11_contract_version(tmp_path: Path) -> None:
    payload = json.loads((ROOT / "examples" / "manifest.example.json").read_text("utf-8"))
    payload["contract_version"] = "component-contract-v1.1.0"
    candidate = tmp_path / "manifest.json"
    candidate.write_text(json.dumps(payload), encoding="utf-8")
    assert validate_document(candidate, ROOT / "schemas" / "manifest.schema.json") == []
