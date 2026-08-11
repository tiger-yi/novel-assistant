# World Bible 运行期结构契约

本规范定义八类 World Bible 在章节事务与 `更新世界` 中的运行期字段、允许动作、禁止动作和证据要求。初始化模板用于创建、第一章前返工/优化候选或修复缺失文件；运行期回写以本契约、当前 `world/*.md`、已发布正文证据和事务变更集为准。

## 1. 通用规则

- 每条新增或更新必须记录稳定 ID、来源章节、正文证据摘要和幂等键。
- 变更集必须写入事务 staging，正式目标只能由事务执行器发布。
- 禁止把 `templates/` 中的示例值、问卷项或创作提示带入正式 World Bible。
- 冲突时按 `state-management.md` 的事实优先级停止并报告，不得静默覆盖。
- 回写顺序遵循 `chapter-summary -> characters -> inventory -> timeline -> geography -> power -> hooks -> outline`。

## 2. 文件职责与动作

| 文件 | 运行期职责 | 允许动作 | 禁止动作 |
| :--- | :--- | :--- | :--- |
| `chapter-summary.md` | 保存已发布章节的检索摘要与承接状态 | 新增或替换同一 `CH-NNNN` 的唯一活跃摘要；更新最近章节窗口与归档索引 | 记录未发布章节事实；覆盖正文事实 |
| `characters.md` | 保存人物当前状态、境界、关系和能力 | 新增 `CHAR-*`；更新境界、状态、关系、技能熟练度、所属势力 | 因改名修改人物 ID；事后新增无正文证据的动机或能力 |
| `inventory.md` | 保存物品、功法、情报、消耗和来源 | 新增 `ITEM-*`；按来源章节扣减数量；更新损毁、失效、归档索引 | 重复扣减；补发正文未获得的道具 |
| `timeline.md` | 保存当前时间节点和重大事件 | 新增 `EVT-*`；更新当前时间；记录闭关、赶路、世界格局变化 | 用模糊时间掩盖因果冲突；重复记录同一事件 |
| `geography.md` | 保存地点、势力、通信和区域状态 | 新增 `LOC-*`、`FAC-*`；更新区域动态、势力状态、通信条件 | 临时新增便利地点或超出既有交通/情报规则 |
| `power.md` | 保存力量体系、境界映射、规则白名单和越级依据 | 新增已在正文或授权规划中引入的体系条目；更新境界、代价、克制关系 | 为通过战斗审计临时降低敌方位格或事后补丁 |
| `hooks.md` | 保存活跃 `HOOK-*` 与 `SEED-*` 叙事线索 | 按 `foreshadowing-spec.md` 创建、推进、解决、回收、放弃、取消和归档索引 | 写入候选线索；缺正文证据或用户批准时跃迁 |
| `outline.md` | 保存未来卷契约与已发布进度统计 | 标记已发布章节完成；更新累计字数、完成章节数、当前进度 | 新增、删除、重排、改写未来章节契约；调整卷区间、卷目标或里程碑 |

## 3. 证据字段

事务变更集中的每项 World Bible 变更至少包含：

- `target`: 目标 World Bible 文件。
- `entity_id`: 章节、人物、物品、事件、地点、势力或叙事线索 ID。
- `action`: `create`、`update`、`consume`、`advance`、`resolve`、`recover`、`archive-index` 或 `stats-update`。
- `source_chapter`: 触发变更的 `CH-NNNN`。
- `old_value`: 已存在字段的原值；新增可为 `null`。
- `new_value`: 候选字段的新值。
- `evidence_summary`: 正文证据摘要或授权说明。
- `idempotency_key`: 由实体 ID、动作和来源章节组成，足以防止重复追加、跃迁或扣减。

## 4. 更新世界约束

`更新世界` 不读取八类初始化模板作为主依据。独立调用时，Agent 必须先基于目标章节生成无冲突变更集，并通过 `prepared-change-set`、`world-audit`、`narrative-thread-integrity` 和周期原创性分类后，才允许事务执行器提交。

## 相关规范

- 状态管理: [state-management.md](state-management.md)
- 世界观审计: [world-audit.md](world-audit.md)
- 叙事线索: [foreshadowing-spec.md](foreshadowing-spec.md)
