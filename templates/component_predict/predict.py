from __future__ import annotations

import argparse
from pathlib import Path

from .io import load_request, write_prediction
from .predictor import build_predictor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--telemetry", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--telemetry-name")
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    request = load_request(args.telemetry, args.metadata, args.telemetry_name)
    prediction = build_predictor(args.checkpoint).predict(request)
    write_prediction(args.output, prediction)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
