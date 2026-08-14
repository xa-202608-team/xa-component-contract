# 组件公共契约（component-contract-v1.0.0）

本契约定义 XA-202608 三个组件仓库（battery / phased-array / wheel）必须遵守的目录结构、命令接口、退出码、输出物、写入边界、数据治理与结论分类。任何组件仓库接入协作流程前，必须先满足本契约。

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

组件必须提供以下三个命令，且行为可被外部编排方直接调用：

```bash
verify
reproduce --mode quick --output /outputs
reproduce --mode full --output /outputs
```

- `verify`：快速自检（依赖安装检查、schema 校验、单元测试），用于 CI 与提交前检查。
- `reproduce --mode quick`：快速端到端复现（小规模数据 / 少量 epoch），分钟级完成。
- `reproduce --mode full`：完整端到端复现，产出与论文/报告一致的最终数字。

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

## 5. 写入边界

- 组件只能写调用方通过 `--output` 指定的输出目录。
- 不得覆盖、修改或删除任何 `reference`（基准参照物）目录 / 文件。
- 不得在组件仓库工作区之外产生副作用写入。

## 6. 数据治理

大型或不可再分发数据不得直接进入 Git：

- 必须在 `manifest.json` 的 `data` 字段登记（name / version / sha256 / redistributable）。
- 必须提供可重复执行的下载或生成脚本（置于 `scripts/`）。
- 必须记录 SHA256 校验和，下载/生成后先行校验再使用。

允许进入 Git 的小型 fixture 必须放在 `tests/fixtures/`，不得用宽泛的 `data/` 例外绕过大文件治理。

## 7. 结论分类

迁移与对比实验的结论只允许以下四类，写入结果文档与 PR 描述：

1. **正迁移**：迁移方案显著优于无迁移基线。
2. **不可分**：差异在统计容差内，无法区分优劣。
3. **无正迁移**：迁移方案不优于基线，但基线未降级。
4. **基线降级**：迁移方案导致基线性能下降（负迁移）。

## 8. 契约校验

本仓库（xa-component-contract）提供 schema 校验器与示例，校验命令见 [README.md](README.md)。组件仓库 CI 必须包含 `contract-validation` 同名工作流，对三个 schema 分别执行校验。
