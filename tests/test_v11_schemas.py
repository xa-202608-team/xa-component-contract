from pathlib import Path

import pytest

from tools.validate_contract import load_document, validate_document


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("document", "schema"),
    [
        ("dataset.example.yaml", "dataset-metadata.schema.json"),
        ("prediction.example.json", "prediction.schema.json"),
        ("handoff_manifest.example.json", "handoff-manifest.schema.json"),
    ],
)
def test_v11_examples_match_schema(document: str, schema: str) -> None:
    assert validate_document(
        ROOT / "examples" / document,
        ROOT / "schemas" / schema,
    ) == []


def test_yaml_loader_reads_dataset_metadata() -> None:
    document = load_document(ROOT / "examples" / "dataset.example.yaml")
    assert document["schema_version"] == "1.1.0"
    assert document["contract_version"] == "component-contract-v1.1.0"


def test_handoff_rejects_short_commit(tmp_path: Path) -> None:
    document = load_document(ROOT / "examples" / "handoff_manifest.example.json")
    document["git_commit"] = "abc1234"
    candidate = tmp_path / "manifest.json"
    candidate.write_text(__import__("json").dumps(document), encoding="utf-8")
    errors = validate_document(candidate, ROOT / "schemas" / "handoff-manifest.schema.json")
    assert any("git_commit" in error for error in errors)
