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
3. 将正式正文复制到事务 staging，由 `draft-worker` 按 `chapter-polish.md` 和当前 `writespec/style-guide.md` 润色。
4. 执行 `signing-first-impression-risk` 门禁；`WARN` 可在等义边界内自动修复，`FAIL` 按四档自动化阻断分级处理。已发布章节只允许等义呈现修订进入 `AUTO_ROUTE_COMMIT`；结构、剧情或 World Bible 风险必须降级为 `AUTO_ROUTE_REVIEW` 或 `HUMAN_REQUIRED`。
5. 运行最终门禁；`presentation-equivalence` 失败时可重润色，最多计入 3 轮。
6. 门禁通过后，事务执行器覆盖正式章节，并只允许同步 `world/chapter-summary.md` 中该章的等义摘要、正文 hash 和证据摘要值。

## 原文基线审计

只检查最低可发布门禁，不重跑完整章节创作门禁：

- `chapter-length`
- `chapter-format`
- `presentation-baseline`
- `world-audit`
- `thread-integrity`

若原正式正文本身存在字数、格式、世界观或叙事线索硬伤，返回 `SOURCE_BASELINE_INVALID` 或 `PREEXISTING_WORLD_ISSUE`。润色命令不得借机修剧情或修 World Bible。

原文关键台词含混作为可修复基线问题记录，不使 `source-baseline` 直接失败；它允许进入等义润色，但最终 staging 必须通过 `dialogue_clarity_audit`。修复无法保持事实、知情范围、决定和关系状态时停止，不得借润色扩写解释。

## 最终门禁

- `chapter-length`: 2300-2800 字。
- `chapter-format`: 满足 `INV-CHAPTER-001`。
- `signing-first-impression-risk`: 润色后正文必须按 `chapter-polish.md` 给出 `signing_first_impression_risk` 证据，覆盖开篇、主要场景入口和章末牵引；接受 `PASS` 或 `WARN` 继续。已发布章节若命中 `L3-ROUTE-AUTO`，只有等义呈现修订可在验证通过后自动提交；影响事件重心、摘要语义、World Bible 或后续契约时，只保留候选预览和推荐路由。
- `presentation-equivalence`: 新旧正文事件、因果、人物行为、资源、伤势和信息差等义，只接受 `PASS`。
- `style-application`: 润色后正文必须证明已应用当前 `writespec/style-guide.md`，产出至少 5 条可定位的 `style_application_evidence`，覆盖核心调性、受限视角/认知偏差、人物声线、节奏或爽点结构、题材质感/黑名单规避；只接受 `PASS`。
- `narrative-integrity`: 不存在叙事层泄漏；同时按 `chapter-creation-spec.md` 提交独立的 `key: reported_speech_audit` 与 `key: dialogue_clarity_audit`。关键台词审计必须绑定最终 staging hash，完整扫描六类风险；零命中也必须提交，只接受 `PASS`。原文问题可进入润色，最终未解决项非空时不得覆盖正式正文。
- `world-audit`: 未引入新世界观冲突。
- `thread-integrity`: 叙事线索状态和证据不变，只接受 `PASS`。

任一必需门禁失败时不覆盖正式正文，不自动修改 World Bible，不自动改剧情；只保留 staging 候选、evidence artifact、失败门禁和恢复点。`style-application` 失败时只允许在等义边界内重润色语言、视角、节奏、排版和质感，不得改变剧情事实、人物决策、胜负、伤势、资源、伏笔状态或 World Bible。`signing-first-impression-risk` 的 `L3-SAFE` 可在等义边界内自动修复；已授权的等义 `L3-ROUTE-AUTO` 可按 `AUTO_ROUTE_COMMIT` 验证提交；`L3-HARD` 必须等待用户再次确认。

## Subagent 输出

subagent 可全量读取仓库，但只允许返回结构化结论、证据定位、artifact 路径/hash、阻断风险和摘要。禁止回传完整正文、完整 World Bible、完整归档片段或完整内部推理。

## 相关规范

- [../chapter-polish.md](../chapter-polish.md)
- [../chapter-creation-spec.md](../chapter-creation-spec.md)
- [../state-management.md](../state-management.md)
- [../world-audit.md](../world-audit.md)
- [../foreshadowing-spec.md](../foreshadowing-spec.md)
