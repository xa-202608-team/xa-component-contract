from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

FORBIDDEN_ROOTS = {"data", "results", "checkpoints"}
ALLOWED_SLOT_FILES = {
    "data/README.md", "data/data_manifest.json",
    "results/README.md", "results/public_summary.json", "results/expected_metrics.json",
    "checkpoints/README.md", "checkpoints/checkpoint_manifest.json",
}
MAX_TRACKED_BYTES = 10 * 1024 * 1024
MAX_FIXTURE_BYTES = 1 * 1024 * 1024
FORBIDDEN_SUFFIXES = {".pt", ".pth", ".ckpt", ".onnx", ".joblib", ".pkl"}

GITHUB_TOKEN_PATTERN = re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}|github_pat_[0-9A-Za-z_]{36,}")
PEM_HEADER_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/](?![\\/])")
CONTENT_SCAN_BYTES = 1 * 1024 * 1024
FIXTURE_PREFIX = "tests/fixtures/"


def _tracked_files(root: Path) -> list[str]:
    """只取 git 索引中的受跟踪文件（posix 相对路径，去重排序）。"""
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    entries = completed.stdout.decode("utf-8", errors="strict").split("\0")
    return sorted({entry.replace("\\", "/") for entry in entries if entry})


def scan_repository(root: Path) -> list[str]:
    """扫描受跟踪文件是否违反公共仓库策略；只报告文件与规则名，不打印秘密原文。"""
    violations: list[str] = []
    for relpath in _tracked_files(root):
        target = root / relpath
        if not target.is_file():
            continue
        violations.extend(_scan_path(relpath, target))
    return sorted(violations)


def _scan_path(relpath: str, target: Path) -> list[str]:
    violations: list[str] = []
    parts = relpath.split("/")
    basename = parts[-1]
    top = parts[0] if len(parts) > 1 else ""

    if top in FORBIDDEN_ROOTS and relpath not in ALLOWED_SLOT_FILES:
        violations.append(f"{relpath}: forbidden-root")
    if target.suffix.lower() in FORBIDDEN_SUFFIXES:
        violations.append(f"{relpath}: forbidden-suffix")
    if basename == ".env" or basename.startswith(".env."):
        violations.append(f"{relpath}: forbidden-env-file")

    try:
        size = target.stat().st_size
    except OSError:
        size = 0
    if relpath.startswith(FIXTURE_PREFIX):
        if size > MAX_FIXTURE_BYTES:
            violations.append(f"{relpath}: oversized-fixture")
    elif size > MAX_TRACKED_BYTES:
        violations.append(f"{relpath}: oversized-file")

    try:
        sample = target.read_bytes()[:CONTENT_SCAN_BYTES]
    except OSError:
        sample = b""
    if sample and b"\x00" not in sample:
        text = sample.decode("utf-8", errors="ignore")
        if GITHUB_TOKEN_PATTERN.search(text):
            violations.append(f"{relpath}: suspected-github-token")
        if PEM_HEADER_PATTERN.search(text):
            violations.append(f"{relpath}: pem-private-key")
        if ABSOLUTE_PATH_PATTERN.search(text):
            violations.append(f"{relpath}: absolute-path")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="公共仓库策略自扫描：只检查 git 受跟踪文件，命中即退出 1（输出仅含文件与规则名）。"
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    violations = scan_repository(args.root)
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
