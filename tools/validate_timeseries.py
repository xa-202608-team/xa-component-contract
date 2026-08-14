from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

REQUIRED_COLUMNS = [
    "timestamp",
    "component_id",
    "component_type",
    "condition_id",
    "telemetry_name",
    "value",
    "unit",
]
FORBIDDEN_LABEL_COLUMNS = {"rul", "label", "degradation_state", "event_observed"}


def validate_telemetry(telemetry_path: Path, metadata: dict) -> list[str]:
    """校验长表遥测 CSV 是否满足 v1.1 时序契约；返回按行号排序的错误列表。"""
    errors: list[tuple[int, str]] = []
    frame = pd.read_csv(telemetry_path)

    for column in REQUIRED_COLUMNS:
        if column not in frame.columns:
            errors.append((0, f"missing-column: {column}"))
    for column in sorted(FORBIDDEN_LABEL_COLUMNS & set(frame.columns)):
        errors.append((0, f"forbidden-label-column: {column}"))
    if errors:
        return _render(errors)

    registry = {item["name"]: item["unit"] for item in metadata.get("telemetry", [])}
    values = pd.to_numeric(frame["value"], errors="coerce")
    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")

    seen_keys: set[tuple[str, str, str]] = set()
    last_timestamp: dict[tuple[str, str], pd.Timestamp] = {}

    for position in range(len(frame)):
        row_number = position + 2  # CSV 行号：第 1 行为表头，数据行从 2 开始
        row = frame.iloc[position]
        name = str(row["telemetry_name"])
        unit = str(row["unit"])
        component = str(row["component_id"])
        raw_timestamp = str(row["timestamp"])

        if pd.isna(values.iloc[position]):
            errors.append((row_number, f"non-numeric-value: {row['value']!r}"))
        current = timestamps.iloc[position]
        if pd.isna(current):
            errors.append((row_number, f"invalid-timestamp: {raw_timestamp}"))
        if name not in registry:
            errors.append((row_number, f"unknown-telemetry: {name}"))
        elif registry[name] != unit:
            errors.append((row_number, f"unit-mismatch: {name} expected {registry[name]} but got {unit}"))

        key = (raw_timestamp, component, name)
        if key in seen_keys:
            errors.append((row_number, f"duplicate-key: ({raw_timestamp}, {component}, {name})"))
        else:
            seen_keys.add(key)

        series_key = (component, name)
        previous = last_timestamp.get(series_key)
        if previous is not None and not pd.isna(current) and current < previous:
            errors.append(
                (row_number, f"time-regression: {raw_timestamp} earlier than {previous.isoformat()} for {component}/{name}")
            )
        if not pd.isna(current):
            last_timestamp[series_key] = current

    return _render(errors)


def _render(errors: list[tuple[int, str]]) -> list[str]:
    ordered = sorted(errors, key=lambda item: (item[0], item[1]))
    return [f"row {row}: {message}" if row > 0 else message for row, message in ordered]


def _load_metadata(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验长表遥测 CSV（配合 dataset.yaml 元数据）：拒绝缺字段/非数值/时间倒退/同键重复/未登记遥测/单位不一致/标签列。"
    )
    parser.add_argument("--telemetry", type=Path, required=True, help="长表遥测 CSV")
    parser.add_argument("--metadata", type=Path, required=True, help="dataset.yaml / dataset.json 元数据")
    args = parser.parse_args()

    metadata = _load_metadata(args.metadata)
    if not isinstance(metadata, dict):
        print("metadata document must be a mapping")
        return 1
    errors = validate_telemetry(args.telemetry, metadata)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
