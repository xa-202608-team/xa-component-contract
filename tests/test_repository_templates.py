from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_contract_documents_define_required_commands() -> None:
    text = (ROOT / "COMPONENT_CONTRACT.md").read_text("utf-8")
    for command in ("verify", "reproduce --mode quick", "reproduce --mode full"):
        assert command in text


def test_pull_request_template_requires_evidence() -> None:
    text = (ROOT / ".github" / "pull_request_template.md").read_text("utf-8")
    for field in ("关联 Issue", "验收命令", "metrics.json", "回退方式"):
        assert field in text


def test_component_gitignore_blocks_generated_artifacts() -> None:
    text = (ROOT / "templates" / "component.gitignore").read_text("utf-8")
    for pattern in ("__pycache__/", ".pytest_cache/", "outputs/", "*.pt", "*.pth"):
        assert pattern in text
