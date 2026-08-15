# xa-component-contract

XA-202608 多仓库协作的公共契约仓库：定义组件复现清单与指标的 JSON Schema、v1.1 时序数据契约（遥测 / 标签 / 数据集元数据 / 预测输出）与 RC 交接清单 Schema、JSON+YAML 双格式校验器、治理模板与契约校验 CI（`contract-validation`）。

## 当前版本

**component-contract-v1.1.0**（分支 `codex/contract-v1.1.0`，向后兼容 v1.0：`manifest.schema.json` 的 `contract_version` 允许 `component-contract-v1.0.0` 与 `component-contract-v1.1.0` 两值，v1.0 存量工件无需变更）。

已发布 Release：**component-contract-v1.0.0** — <https://github.com/xa-202608-team/xa-component-contract/releases/tag/component-contract-v1.0.0>

## 文档导航

- [COMPONENT_CONTRACT.md](COMPONENT_CONTRACT.md) — 组件公共契约正文（目录 / 命令 / 退出码 / 输出物 / 写入边界 / 数据治理 / 结论分类 / v1.1 时序数据契约 / RC 交接清单 / 工件层级）
- Schema（v1.0）：
  - [schemas/manifest.schema.json](schemas/manifest.schema.json)
  - [schemas/metrics.schema.json](schemas/metrics.schema.json)
  - [schemas/expected_metrics.schema.json](schemas/expected_metrics.schema.json)
- Schema（v1.1 新增）：
  - [schemas/telemetry.schema.json](schemas/telemetry.schema.json)
  - [schemas/labels.schema.json](schemas/labels.schema.json)
  - [schemas/dataset-metadata.schema.json](schemas/dataset-metadata.schema.json)
  - [schemas/prediction.schema.json](schemas/prediction.schema.json)
  - [schemas/handoff-manifest.schema.json](schemas/handoff-manifest.schema.json)
- 示例（v1.0）：
  - [examples/manifest.example.json](examples/manifest.example.json)
  - [examples/metrics.example.json](examples/metrics.example.json)
  - [examples/expected_metrics.example.json](examples/expected_metrics.example.json)
- 示例（v1.1 新增）：
  - [examples/telemetry_long.example.csv](examples/telemetry_long.example.csv)
  - [examples/labels.example.csv](examples/labels.example.csv)
  - [examples/dataset.example.yaml](examples/dataset.example.yaml)
  - [examples/prediction.example.json](examples/prediction.example.json)
  - [examples/handoff_manifest.example.json](examples/handoff_manifest.example.json)
- 组件仓库模板：[templates/component.gitignore](templates/component.gitignore)、[templates/component-CODEOWNERS](templates/component-CODEOWNERS)

## 本地校验

校验器 `tools/validate_contract.py` 通过 `load_document` 同时支持 JSON 与 YAML 文档（按扩展名分流，`.yaml` / `.yml` / `.json`）。

```bash
python tools/validate_contract.py --schema schemas/manifest.schema.json --input examples/manifest.example.json
python tools/validate_contract.py --schema schemas/handoff-manifest.schema.json --input examples/handoff_manifest.example.json
python tools/validate_contract.py --schema schemas/dataset-metadata.schema.json --input examples/dataset.example.yaml
pytest -q
```

## CI

`.github/workflows/validate.yml` 定义 `contract-validation` 工作流：安装 `requirements-dev.lock` 锁定依赖后运行全量测试，并对各 schema 的示例执行校验。
