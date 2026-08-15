# 组件公共契约（component-contract-v1.1.0）

本契约定义 XA-202608 三个组件仓库（battery / phased-array / wheel）必须遵守的目录结构、命令接口、退出码、输出物、写入边界、数据治理、时序数据契约、RC 交接清单与结论分类。任何组件仓库接入协作流程前，必须先满足本契约。

本版本为 **component-contract-v1.1.0**，向后兼容 **component-contract-v1.0.0**：`schemas/manifest.schema.json` 的 `contract_version` 允许取两值，v1.0 存量工件（manifest / metrics / expected_metrics）无需任何变更即可继续通过校验；v1.1 新增的时序输入与 RC 清单契约见第 9–11 节。

## 1. 目录结构

每个组件仓库的顶层目录固定为：

```text
README.md
Dockerfile
requirements.lock
configs/
src/
tests/
scripts/
docs/
```

说明：

- `configs/`：组件级 YAML 配置，所有超参数集中于此，不得在代码中散落硬编码。
- `src/`：核心实现（仿真、模型、训练、迁移）。
- `tests/`：pytest 测试；小型 fixture 必须放在 `tests/fixtures/`。
- `scripts/`：数据下载、审计与端到端运行入口。
- `docs/`：组件内文档（结果、复现说明等）。

## 2. 命令接口

组件必须提供以下三个 v1.0 命令，且行为可被外部编排方直接调用：

```bash
verify
reproduce --mode quick --output /outputs
reproduce --mode full --output /outputs
```

- `verify`：快速自检（依赖安装检查、schema 校验、单元测试），用于 CI 与提交前检查。
- `reproduce --mode quick`：快速端到端复现（小规模数据 / 少量 epoch），分钟级完成。
- `reproduce --mode full`：完整端到端复现，产出与论文/报告一致的最终数字。

自 component-contract-v1.1.0 起，另须提供以下命令：

```bash
verify
reproduce_judge --output $OUTPUT_DIR
reproduce_full --output $OUTPUT_DIR
python -m component.predict --telemetry $TELEMETRY_CSV --metadata $DATASET_YAML --output $OUTPUT_DIR
```

- `reproduce_judge`：评审用小规模端到端复现（对齐 `reproduce --mode quick` 定位），结果写入 `$OUTPUT_DIR`。
- `reproduce_full`：完整端到端复现（对齐 `reproduce --mode full` 定位），RC 交接前必须通过。
- `python -m component.predict`：离线单次预测入口；`--telemetry` 输入符合 `schemas/telemetry.schema.json` 的遥测 CSV，`--metadata` 输入符合 `schemas/dataset-metadata.schema.json` 的元数据 YAML（JSON 亦可），输出符合 `schemas/prediction.schema.json` 的预测文档到 `$OUTPUT_DIR`。

## 3. 退出码

- `0`：成功。
- 非 `0`：失败。任何一步失败必须以非零退出码终止，不得"带病"返回 0。

## 4. 输出物

`reproduce` 运行结束后，`--output` 指定目录内必须包含：

- `manifest.json`：复现清单（代码版本、数据版本与 SHA256、随机种子、环境），符合 `schemas/manifest.schema.json`。
- `metrics.json`：指标结果，符合 `schemas/metrics.schema.json`。
- `run.log`：完整运行日志。
- `figures/`：结果图表目录。
- `REPRODUCE_OK`：仅在整条流程成功结束时写出的哨兵文件。

v1.1 起，RC 候选工件另需附交接清单（见第 10 节），`python -m component.predict` 的输出物见第 9.3 节。

## 5. 写入边界

- 组件只能写调用方通过 `--output` 指定的输出目录。
- 不得覆盖、修改或删除任何 `reference`（基准参照物）目录 / 文件。
- 不得在组件仓库工作区之外产生副作用写入。

## 6. 数据治理

大型或不可再分发数据不得直接进入 Git：

- 必须在 `manifest.json` 的 `data` 字段登记（name / version / sha256 / redistributable）。
- 必须提供可重复执行的下载或生成脚本（置于 `scripts/`）。
- 必须记录 SHA256 校验和，下载/生成后先行校验再使用。
- v1.1 起，数据集元数据（第 9.2 节）中的 `sources[]` 与 RC 清单（第 10 节）中的 `files[]` 必须逐项登记 `source_url`：外部数据使用合法 `https` URL；纯本地仿真生成允许 `null`，但 `processing_provenance` 必须给出配置、脚本和种子，不得用空字符串规避溯源。

允许进入 Git 的小型 fixture 必须放在 `tests/fixtures/`，不得用宽泛的 `data/` 例外绕过大文件治理。

## 7. 结论分类

迁移与对比实验的结论只允许以下四类，写入结果文档与 PR 描述：

1. **正迁移**：迁移方案显著优于无迁移基线。
2. **不可分**：差异在统计容差内，无法区分优劣。
3. **无正迁移**：迁移方案不优于基线，但基线未降级。
4. **基线降级**：迁移方案导致基线性能下降（负迁移）。

## 8. 契约校验

本仓库（xa-component-contract）提供 schema 校验器与示例，校验命令见 [README.md](README.md)。校验器 `tools/validate_contract.py` 同时支持 JSON 与 YAML 输入（`load_document` 按扩展名分流）。组件仓库 CI 必须包含 `contract-validation` 同名工作流，对本仓库全部 schema 分别执行校验：v1.0 三个（`manifest` / `metrics` / `expected_metrics`）与 v1.1 五个（`telemetry` / `labels` / `dataset-metadata` / `prediction` / `handoff-manifest`）。

## 9. v1.1 时序数据契约

时序输入必须遵守"遥测与标签分离"：观测（遥测）与监督信号（标签）是两张独立表，标签由预处理流程统一派生（HI / SOH / RUL 均非数据集原始字段），不得混入遥测表，杜绝标签泄漏。

### 9.1 遥测表与标签表

- 遥测表（CSV）：每行一条观测，列固定为 `timestamp,component_id,component_type,condition_id,telemetry_name,value,unit`，符合 `schemas/telemetry.schema.json`；`component_type` 只允许 `battery|phased_array|wheel`。示例：`examples/telemetry_long.example.csv`。
- 标签表（CSV）：每行一条标签，必填 `timestamp,component_id,degradation_state,split`，可选 `rul,event_observed,rul_lower_bound`；`split` 只允许 `train|validation|test|inference`，符合 `schemas/labels.schema.json`。示例：`examples/labels.example.csv`。
- 两表以 `(timestamp, component_id)` 对齐；个体划分（train/val/test）必须按 `component_id` 整体划分，同一退化轨迹不得跨 split 泄漏。

### 9.2 数据集元数据

每个数据集必须附一份元数据文档（YAML 或 JSON），符合 `schemas/dataset-metadata.schema.json`，登记：时间轴（`time`）、遥测通道（`telemetry[]`：单位 / 采样频率 / 来源 / 预测时可获得性 / 是否派生 / 退化方向）、缺失规则（`missing_values`）、按 `component_id` 的划分（`split`）、标签派生依据（`labels`）、数据来源（`sources[]`：名称 / 版本 / URL / 许可 / SHA256 / 处理脚本）与预测设定（`prediction`：主遥测 / 退化方向 / 失效阈值 / 预测步数 / RUL 单位）。示例：`examples/dataset.example.yaml`。

### 9.3 预测输出

`python -m component.predict` 的输出文档必须符合 `schemas/prediction.schema.json`：登记 `schema_version / contract_version / component / git_commit / telemetry_name / generated_at / forecasts / status`，其中 `forecasts[]` 逐条给出 `component_id, origin_timestamp, horizon_step, predicted_timestamp, predicted_value, unit`，可选 `rul, rul_unit, uncertainty_lower, uncertainty_upper`。示例：`examples/prediction.example.json`。

## 10. RC 交接清单

每个正式 RC（release candidate）必须附一份交接清单，符合 `schemas/handoff-manifest.schema.json`：登记 `release_candidate`（形如 `<component>-vX.Y.Z-rc.N`）、`git_commit`（40 位十六进制）、环境、随机种子、复现命令（`commands`）、公开摘要（`public_summary`）与 `reproduce_status`，并对工件 `files[]` 逐文件登记 `path / role / size / sha256 / redistributable / source_url / processing_provenance`。溯源规则与第 6 节一致：外部数据必须 `https` URL，本地仿真生成允许 `null` 但必须给出配置、脚本和种子的处理溯源，不得用空字符串规避。示例：`examples/handoff_manifest.example.json`。

## 11. 工件层级

工件按可信度与可变性分为四层，任何协作引用必须先声明所在层级：

| 层级 | 定义 | 可变性 | 用途 |
|------|------|--------|------|
| 代码 CI | 每次 push / PR 触发的 `contract-validation` 与 `verify` | 每次提交都会重跑 | 只证明代码当下可测通过，不产出对外工件 |
| 未打标签 `main` 候选 | 已合入 `main` 但未打任何 RC / 版本标签的提交 | 随合入随时变动 | 内部集成预览，不作为评审或比对基准 |
| 正式 RC 工件 | 以 `<component>-vX.Y.Z-rc.N` 命名、附第 10 节交接清单的候选版本 | 工件内容冻结（git_commit 固定） | 评审、跨仓库比对与总集成验收 |
| 不可变 Tag | 正式发布标签（组件版本 tag 与 `component-contract-vX.Y.Z` 契约 tag） | 不可改写 | 长期引用基准；任何变更必须走新版本号，禁止移动已有 tag |
