# RC 交接手册（handoff）模板

各组件仓库发布正式 RC（`<component>-vX.Y.Z-rc.N`）时，把本目录模板复制到组件仓库并逐项填写。
交接物必须符合 component-contract-v1.1.0（见 COMPONENT_CONTRACT.md 第 10–11 节）。

## 交接步骤

1. **冻结候选**：确认 `git_commit` 为 40 位十六进制完整哈希，交接期间不得移动该提交。
2. **完整复现**：`reproduce_full --output $OUTPUT_DIR` 必须成功，产出 `manifest.json`、`metrics.json`、
   `run.log`、`figures/`、`REPRODUCE_OK`。
3. **填写交接清单**：按 `schemas/handoff-manifest.schema.json` 生成 handoff manifest
   （登记环境、随机种子、复现命令、`files[]` 逐文件 `path/role/size/sha256/redistributable/
   source_url/processing_provenance`、`public_summary` 与 `reproduce_status`）。
4. **登记槽位文件**：填写 `data/data_manifest.json`、`results/public_summary.json`、
   `results/expected_metrics.json`、`checkpoints/checkpoint_manifest.json`；这些是数据 / 结果 /
   权重三个只读槽位中仅允许入库的占位文件（白名单见 `tools/repository_policy.py` 的
   `ALLOWED_SLOT_FILES`）。
5. **对齐工件映射**：按 `artifact-map.yaml` 声明每个产物由哪条命令产生、落在哪个槽位、属于哪一层级。
6. **结论分类**：迁移与对比实验结论只允许四类之一——正迁移 / 不可分 / 无正迁移 / 基线降级。

## 硬性红线

- 不可再分发数据与模型权重禁止进入 Git；溯源规则：外部数据必须 `https` 的 `source_url`，
  本地仿真生成允许 `null` 但必须给出配置、脚本和种子的 `processing_provenance`。
- `git_commit`、`sha256`、`random_seeds` 缺一不可；`reproduce_status` 只允许 `REPRODUCE_OK`。
- PR 未合并、`component-contract-v1.1.0` Tag 未创建前，不得把 v1.1 标为正式依赖。
