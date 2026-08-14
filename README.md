# xa-component-contract

XA-202608 多仓库协作的公共契约仓库：定义组件复现清单与指标的 JSON Schema、校验器、治理模板与契约校验 CI（`contract-validation`）。

## 当前版本

**component-contract-v1.0.0** — 首个正式版本，Release 见：<https://github.com/xa-202608-team/xa-component-contract/releases/tag/component-contract-v1.0.0>

## 文档导航

- [COMPONENT_CONTRACT.md](COMPONENT_CONTRACT.md) — 组件公共契约正文（目录 / 命令 / 退出码 / 输出物 / 写入边界 / 数据治理 / 结论分类）
- Schema：
  - [schemas/manifest.schema.json](schemas/manifest.schema.json)
  - [schemas/metrics.schema.json](schemas/metrics.schema.json)
  - [schemas/expected_metrics.schema.json](schemas/expected_metrics.schema.json)
- 示例：
  - [examples/manifest.example.json](examples/manifest.example.json)
  - [examples/metrics.example.json](examples/metrics.example.json)
  - [examples/expected_metrics.example.json](examples/expected_metrics.example.json)
- 组件仓库模板：[templates/component.gitignore](templates/component.gitignore)、[templates/component-CODEOWNERS](templates/component-CODEOWNERS)

## 本地校验

```bash
python tools/validate_contract.py --schema schemas/manifest.schema.json --input examples/manifest.example.json
pytest -q
```

## CI

`.github/workflows/validate.yml` 定义 `contract-validation` 工作流：安装 `requirements-dev.lock` 锁定依赖后运行全量测试，并对三个 schema 各自的示例执行校验。
