import json
from pathlib import Path

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
