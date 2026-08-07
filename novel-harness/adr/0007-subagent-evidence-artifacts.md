# ADR 0007: Subagents Produce Evidence Artifacts Only

## Status

Accepted

## Context

章节创作、世界更新、初始化、风格创建、归档和正式正文润色会读取大量正文、World Bible 与历史归档。若所有审计、候选生成和证据整理都回灌主窗口，主 agent 的上下文会快速膨胀，并增加恢复时误用陈旧推理的风险。

同时，项目已有事务边界要求：正式章节、World Bible、归档、风格和报告目标只能由事务执行器提交。subagent 化不能改变这个权威模型。

## Decision

Manifest 可以声明可选 delegation 策略。subagent 可全量读取仓库，并在授权范围内生成事务 staging、候选变更集、归档预览或语义门禁证据。

subagent 的正式输出是 `evidence artifact`：包含任务、状态、artifact 路径/hash、证据定位、阻断风险和摘要的可复核文件。subagent 不得回传完整正文、完整 World Bible、完整归档片段或完整内部推理。

主 agent 只复核 artifact schema、路径和 hash，并汇总门禁状态、风险和恢复点。事务执行器仍是唯一正式提交者。

## Consequences

- 主窗口只承载决策摘要和 artifact 指针，减少上下文污染。
- 大上下文读取可以下放给固定 worker 角色，但结论必须可复核。
- 任一 subagent 返回 `FAIL` 或 schema 无效时，主 agent 停止提交并报告阻断证据。
- 调度策略放在 Manifest 层，命令协议只保留语义边界和门禁要求。
