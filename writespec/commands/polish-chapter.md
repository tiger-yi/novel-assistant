# 命令协议: 润色章节 (polish-chapter)

> **正式正文润色**: `润色章节 CH-0001`
>
> **事务内润色**: `润色当前章节`

## 功能

`润色章节 CH-NNNN` 对已发布正文创建新的 `TX-CH-NNNN-RNN` 等义呈现修订事务。目标是改善语言质感、节奏、物理化描写和去 AI 工业感，最终可由事务执行器覆盖正式章节。

`润色当前章节` 只用于已有活跃章节事务内的 staging 正文。找不到活跃 staging 时返回 `STAGING_NOT_FOUND`，只提示继续创作事务、改用 `润色章节 CH-NNNN` 或指定正确事务，不自动从正式正文创建 staging。

## 边界

- Agent 或 subagent 只写事务专属 staging 和 evidence artifact。
- 正式章节、摘要索引和证据摘要值只能由事务执行器提交。
- 禁止改变剧情事实、角色决策、物品消耗、伤势结果、信息差、叙事线索状态、World Bible 事实和大纲契约。
- `draft-worker` 可直接改写 `chapters/.staging/<TX>/` 内目标正文，但不得回传正文全文。
- 单次命令最多 3 轮自动润色；任一轮发现事实风险立即停止。

## 正式正文润色流程

1. 事务执行器严格解析 `润色章节 CH-NNNN`，创建下一 `TX-CH-NNNN-RNN`。
2. 执行原文基线审计；失败返回 `SOURCE_BASELINE_INVALID`，不进入润色。
3. 将正式正文复制到事务 staging，由 `draft-worker` 按 `chapter-polish.md` 润色。
4. 运行最终门禁；`presentation-equivalence` 失败时可重润色，最多计入 3 轮。
5. 门禁通过后，事务执行器覆盖正式章节，并只允许同步 `world/chapter-summary.md` 中该章的等义摘要、正文 hash 和证据摘要值。

## 原文基线审计

只检查最低可发布门禁，不重跑完整章节创作门禁：

- `chapter-length`
- `chapter-format`
- `presentation-baseline`
- `world-audit`
- `thread-integrity`

若原正式正文本身存在字数、格式、世界观或叙事线索硬伤，返回 `SOURCE_BASELINE_INVALID` 或 `PREEXISTING_WORLD_ISSUE`。润色命令不得借机修剧情或修 World Bible。

## 最终门禁

- `chapter-length`: 2300-2800 字。
- `chapter-format`: 满足 `INV-CHAPTER-001`。
- `presentation-equivalence`: 新旧正文事件、因果、人物行为、资源、伤势和信息差等义，只接受 `PASS`。
- `narrative-integrity`: 不存在叙事层泄漏，只接受 `PASS`。
- `world-audit`: 未引入新世界观冲突。
- `thread-integrity`: 叙事线索状态和证据不变，只接受 `PASS`。

任一必需门禁失败时不覆盖正式正文，不自动修改 World Bible，不自动改剧情；只保留 staging 候选、evidence artifact、失败门禁和恢复点。

## Subagent 输出

subagent 可全量读取仓库，但只允许返回结构化结论、证据定位、artifact 路径/hash、阻断风险和摘要。禁止回传完整正文、完整 World Bible、完整归档片段或完整内部推理。

## 相关规范

- [../chapter-polish.md](../chapter-polish.md)
- [../chapter-creation-spec.md](../chapter-creation-spec.md)
- [../state-management.md](../state-management.md)
- [../world-audit.md](../world-audit.md)
- [../foreshadowing-spec.md](../foreshadowing-spec.md)
