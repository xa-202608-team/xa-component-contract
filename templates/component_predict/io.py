from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

FORBIDDEN_INFERENCE_COLUMNS = {"rul", "label", "degradation_state", "event_observed", "rul_lower_bound"}


@dataclass(frozen=True)
class PredictionRequest:
    telemetry: pd.DataFrame
    metadata: dict
    telemetry_name: str


def load_request(telemetry_path: Path, metadata_path: Path, requested_name: str | None) -> PredictionRequest:
    frame = pd.read_csv(telemetry_path)
    forbidden = sorted(FORBIDDEN_INFERENCE_COLUMNS & set(frame.columns))
    if forbidden:
        raise ValueError(f"labels are forbidden in inference telemetry: {forbidden}")
    metadata = yaml.safe_load(metadata_path.read_text("utf-8"))
    name = requested_name or metadata["prediction"]["primary_telemetry"]
    selected = frame.loc[frame["telemetry_name"] == name].copy()
    if selected.empty:
        raise ValueError(f"telemetry not found: {name}")
    selected["timestamp"] = pd.to_datetime(selected["timestamp"], utc=True, errors="raise")
    selected = selected.sort_values(["component_id", "timestamp"], kind="stable")
    return PredictionRequest(selected, metadata, name)


def write_prediction(output_path: Path, prediction: dict) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(prediction, ensure_ascii=False, indent=2, sort_keys=True)
    (output_path / "prediction.json").write_text(payload + "\n", encoding="utf-8")
