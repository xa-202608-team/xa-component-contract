from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

DEFAULT_ID_COLUMNS = ["timestamp", "component_id", "component_type", "condition_id"]


def wide_to_long(frame, id_columns, telemetry_units):
    missing = sorted(set(id_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"missing id columns: {missing}")
    telemetry = sorted(set(frame.columns) - set(id_columns))
    unknown = sorted(set(telemetry) - set(telemetry_units))
    if unknown:
        raise ValueError(f"missing units for: {unknown}")
    long = frame.melt(
        id_vars=id_columns,
        value_vars=telemetry,
        var_name="telemetry_name",
        value_name="value",
    )
    long["unit"] = long["telemetry_name"].map(telemetry_units)
    return long.sort_values(id_columns + ["telemetry_name"], kind="stable").reset_index(drop=True)


def _load_units(spec: str) -> dict[str, str]:
    """解析 --units-json：内联 JSON 对象或指向 JSON 文件的路径。"""
    text = spec.strip()
    if not text.startswith("{"):
        text = Path(spec).read_text(encoding="utf-8")
    units = json.loads(text)
    if not isinstance(units, dict) or not all(
        isinstance(name, str) and isinstance(unit, str) for name, unit in units.items()
    ):
        raise ValueError("--units-json must be a JSON object mapping telemetry columns to unit strings")
    return units


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "把宽表遥测 CSV 确定性地转换为契约长表 "
            "(timestamp,component_id,component_type,condition_id,telemetry_name,value,unit)。"
            "单位必须经 --units-json 显式给定，禁止按列名猜测。"
        )
    )
    parser.add_argument("--input", type=Path, required=True, help="宽表遥测 CSV 输入")
    parser.add_argument("--output", type=Path, required=True, help="长表 CSV 输出")
    parser.add_argument(
        "--units-json",
        required=True,
        help='遥测列到单位的 JSON 映射，支持内联对象（如 \'{"voltage": "V"}\'）或 JSON 文件路径',
    )
    parser.add_argument("--id-columns", nargs="+", default=DEFAULT_ID_COLUMNS)
    args = parser.parse_args()

    units = _load_units(args.units_json)
    frame = pd.read_csv(args.input)
    long = wide_to_long(frame, list(args.id_columns), units)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    long.to_csv(args.output, index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
