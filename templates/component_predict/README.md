# component_predict 组件预测入口模板

本模板实现契约 `python -m component.predict` 命令（见 COMPONENT_CONTRACT.md 第 2 节与第 9.3 节）。
复制到组件仓库根目录并重命名为 `component/` 包：

```bash
cp -r templates/component_predict <组件仓库>/component
```

## 文件说明

- `predict.py`：只负责参数解析与调用，不放任何组件算法。
- `io.py`：定义不可变请求对象 `PredictionRequest`，并在模型调用前完成标签隔离
  （`FORBIDDEN_INFERENCE_COLUMNS` 命中即拒绝，杜绝标签泄漏）。
- `predictor.py`：**必须由各组件仓库自行实现，本模板不提供，也不得提交只会抛"未实现"异常的空壳。**

## predictor.py 实现要求

组件仓库需实现并提交 `component/predictor.py`：

```python
def build_predictor(checkpoint): ...
```

返回值须提供 `predict(request: PredictionRequest) -> dict`，输出 dict 必须符合
`schemas/prediction.schema.json`（`schema_version / contract_version / component /
git_commit / telemetry_name / generated_at / forecasts / status`）。加载 checkpoint 失败必须
以非零退出码失败，不得回退到无权重路径。

## 使用方式

```bash
python -m component.predict \
  --telemetry data/telemetry.csv \
  --metadata data/dataset.yaml \
  --output $OUTPUT_DIR \
  --checkpoint checkpoints/model.ckpt
```

- `--telemetry`：符合 `schemas/telemetry.schema.json` 的长表遥测 CSV。
- `--metadata`：符合 `schemas/dataset-metadata.schema.json` 的元数据 YAML/JSON；
  未显式给 `--telemetry-name` 时取 `prediction.primary_telemetry`。
- 输出：`$OUTPUT_DIR/prediction.json`（UTF-8、`sort_keys=True`）。
