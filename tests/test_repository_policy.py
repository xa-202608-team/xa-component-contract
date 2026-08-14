import subprocess
from pathlib import Path

from tools.repository_policy import scan_repository


ROOT = Path(__file__).resolve().parents[1]


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    return root


def _track(root: Path, relpath: str, content: bytes = b"placeholder\n") -> None:
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    subprocess.run(["git", "add", relpath], cwd=root, check=True, capture_output=True)


def test_scan_ignores_untracked_files(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    (root / "data").mkdir()
    (root / "data" / "private.csv").write_bytes(b"secret,1\n")
    assert scan_repository(root) == []


def test_scan_blocks_data_root_files(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    _track(root, "data/private.csv")
    violations = scan_repository(root)
    assert "data/private.csv: forbidden-root" in violations


def test_scan_blocks_github_token(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    token = ("ghp_" + "a1b2c3d4e5" * 4).encode("ascii")
    _track(root, "src/settings.py", b'token = "' + token + b'"\n')
    violations = scan_repository(root)
    assert any(violation == "src/settings.py: suspected-github-token" for violation in violations)
    assert not any(token.decode("ascii") in violation for violation in violations)


def test_scan_blocks_pem_private_key_header(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    pem = b"-----BEGIN RSA PRIVATE" + b" KEY-----\nMIIB\n"
    _track(root, "keys/server.key", pem)
    violations = scan_repository(root)
    assert any(violation == "keys/server.key: pem-private-key" for violation in violations)


def test_scan_blocks_absolute_windows_path(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    payload = b"cache_dir = " + ("D:" + "\\Workspace" + "\\private").encode("ascii")
    _track(root, "configs/local.py", payload)
    violations = scan_repository(root)
    assert any(violation == "configs/local.py: absolute-path" for violation in violations)


def test_scan_blocks_oversized_tracked_file(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    _track(root, "assets/blob.bin", b"0" * (11 * 1024 * 1024))
    violations = scan_repository(root)
    assert any(violation == "assets/blob.bin: oversized-file" for violation in violations)


def test_scan_blocks_env_file_and_weight_suffixes(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    _track(root, ".env", b"TOKEN=secret\n")
    _track(root, "models/weights.pt", b"\x00\x01\x02")
    violations = scan_repository(root)
    assert ".env: forbidden-env-file" in violations
    assert "models/weights.pt: forbidden-suffix" in violations


def test_scan_allows_slot_files_and_small_fixtures(tmp_path: Path) -> None:
    root = _init_repo(tmp_path / "repo")
    _track(root, "data/README.md")
    _track(root, "data/data_manifest.json")
    _track(root, "results/README.md")
    _track(root, "results/public_summary.json")
    _track(root, "results/expected_metrics.json")
    _track(root, "checkpoints/README.md")
    _track(root, "checkpoints/checkpoint_manifest.json")
    _track(root, "tests/fixtures/tiny.csv", b"a,b\n1,2\n")
    assert scan_repository(root) == []


def test_component_gitignore_template_covers_slot_whitelist() -> None:
    text = (ROOT / "templates" / "component.gitignore").read_text("utf-8")
    required_patterns = [
        "/data/**",
        "!/data/README.md",
        "!/data/data_manifest.json",
        "/results/**",
        "!/results/README.md",
        "!/results/public_summary.json",
        "!/results/expected_metrics.json",
        "/checkpoints/**",
        "!/checkpoints/README.md",
        "!/checkpoints/checkpoint_manifest.json",
        "/reference/data/**",
        "/reference/models/**",
        "/reference/results/**",
        "/release/data/**",
        "/release/checkpoints/**",
        "/release/results/**",
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".venv/",
        ".private/",
        "*.log",
        "*.pt",
        "*.pth",
        "*.ckpt",
        ".env",
        ".env.*",
    ]
    for pattern in required_patterns:
        assert pattern in text, f"component.gitignore missing pattern: {pattern}"
