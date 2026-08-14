import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from tools.convert_wide_to_long import wide_to_long


ROOT = Path(__file__).resolve().parents[1]

ID_COLUMNS = ["timestamp", "component_id", "component_type", "condition_id"]


def test_wide_to_long_is_deterministic() -> None:
    wide = pd.DataFrame({
        "timestamp": ["2026-01-01T00:00:00Z"],
        "component_id": ["wheel-001"],
        "component_type": ["wheel"],
        "condition_id": ["nominal"],
        "motor_current": [0.8],
        "wheel_speed": [3200.0],
    })
    long = wide_to_long(
        wide,
        id_columns=["timestamp", "component_id", "component_type", "condition_id"],
        telemetry_units={"motor_current": "A", "wheel_speed": "rpm"},
    )
    assert list(long["telemetry_name"]) == ["motor_current", "wheel_speed"]
    assert list(long["unit"]) == ["A", "rpm"]
    assert "rul" not in long.columns


def test_wide_to_long_sorts_telemetry_by_name() -> None:
    wide = pd.DataFrame({
        "timestamp": ["2026-01-01T00:00:00Z"],
        "component_id": ["wheel-001"],
        "component_type": ["wheel"],
        "condition_id": ["nominal"],
        "wheel_speed": [3200.0],
        "motor_current": [0.8],
    })
    long = wide_to_long(wide, id_columns=ID_COLUMNS, telemetry_units={"motor_current": "A", "wheel_speed": "rpm"})
    assert list(long["telemetry_name"]) == ["motor_current", "wheel_speed"]


def test_wide_to_long_rejects_missing_id_columns() -> None:
    wide = pd.DataFrame({"timestamp": ["2026-01-01T00:00:00Z"], "voltage": [28.4]})
    with pytest.raises(ValueError, match="missing id columns"):
        wide_to_long(wide, id_columns=["timestamp", "component_id"], telemetry_units={"voltage": "V"})


def test_wide_to_long_rejects_telemetry_without_units() -> None:
    wide = pd.DataFrame({
        "timestamp": ["2026-01-01T00:00:00Z"],
        "component_id": ["battery-001"],
        "component_type": ["battery"],
        "condition_id": ["nominal"],
        "voltage": [28.4],
        "current": [0.8],
    })
    with pytest.raises(ValueError, match="missing units for: \\['current'\\]"):
        wide_to_long(wide, id_columns=ID_COLUMNS, telemetry_units={"voltage": "V"})


def test_convert_cli_reads_explicit_units_json_file(tmp_path: Path) -> None:
    wide_csv = tmp_path / "wide.csv"
    wide_csv.write_text(
        "timestamp,component_id,component_type,condition_id,voltage\n"
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,28.4\n",
        encoding="utf-8",
    )
    units_file = tmp_path / "units.json"
    units_file.write_text('{"voltage": "V"}', encoding="utf-8")
    output_csv = tmp_path / "out" / "long.csv"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_wide_to_long.py"),
            "--input", str(wide_csv),
            "--output", str(output_csv),
            "--units-json", str(units_file),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    long = pd.read_csv(output_csv)
    assert list(long["telemetry_name"]) == ["voltage"]
    assert list(long["unit"]) == ["V"]


def test_convert_cli_fails_without_units_json(tmp_path: Path) -> None:
    wide_csv = tmp_path / "wide.csv"
    wide_csv.write_text(
        "timestamp,component_id,component_type,condition_id,voltage\n"
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,28.4\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_wide_to_long.py"),
            "--input", str(wide_csv),
            "--output", str(tmp_path / "long.csv"),
        ],
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
