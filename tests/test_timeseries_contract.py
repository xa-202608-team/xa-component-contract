from pathlib import Path

from tools.validate_timeseries import validate_telemetry


HEADER = "timestamp,component_id,component_type,condition_id,telemetry_name,value,unit"

METADATA = {
    "telemetry": [
        {"name": "voltage", "unit": "V"},
        {"name": "current", "unit": "A"},
    ],
}


def _write_csv(path: Path, *rows: str, header: str = HEADER) -> Path:
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def test_valid_long_table_passes(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V",
        "2026-01-01T00:01:00Z,battery-001,battery,nominal,voltage,28.3,V",
    )
    assert validate_telemetry(telemetry, METADATA) == []


def test_rejects_missing_required_columns(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,voltage,28.4",
        header="timestamp,component_id,component_type,telemetry_name,value",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any(error == "missing-column: condition_id" for error in errors)
    assert any(error == "missing-column: unit" for error in errors)


def test_rejects_non_numeric_value(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,broken,V",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("non-numeric-value" in error for error in errors)


def test_rejects_time_regression_within_component(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:01:00Z,battery-001,battery,nominal,voltage,28.3,V",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("time-regression" in error for error in errors)


def test_allows_same_timestamp_across_components(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V",
        "2026-01-01T00:00:00Z,battery-002,battery,nominal,voltage,28.1,V",
    )
    assert validate_telemetry(telemetry, METADATA) == []


def test_rejects_duplicate_key(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("duplicate-key" in error for error in errors)


def test_rejects_unregistered_telemetry_name(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,temperature,25.0,K",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("unknown-telemetry: temperature" in error for error in errors)


def test_rejects_unit_mismatch(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,mV",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("unit-mismatch" in error for error in errors)


def test_rejects_label_columns_in_telemetry(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V,720",
        header=HEADER + ",rul",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("forbidden-label-column: rul" in error for error in errors)


def test_rejects_label_names_as_telemetry(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,rul,720,minutes",
    )
    errors = validate_telemetry(telemetry, METADATA)
    assert any("unknown-telemetry: rul" in error for error in errors)


def test_errors_are_sorted_by_row_number(tmp_path: Path) -> None:
    telemetry = _write_csv(
        tmp_path / "telemetry.csv",
        "2026-01-01T00:00:00Z,battery-001,battery,nominal,voltage,28.4,V",
        "2026-01-01T00:01:00Z,battery-001,battery,nominal,temperature,25.0,K",
        "2026-01-01T00:02:00Z,battery-001,battery,nominal,voltage,broken,V",
        "2026-01-01T00:03:00Z,battery-001,battery,nominal,voltage,28.4,mV",
    )
    errors = validate_telemetry(telemetry, METADATA)
    row_numbers = [int(error.split(":")[0].split()[1]) for error in errors]
    assert row_numbers == sorted(row_numbers)
    assert row_numbers[0] == 3
