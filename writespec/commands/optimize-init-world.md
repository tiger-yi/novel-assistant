# 命令协议: 优化初始化世界 (optimize-init-world)

**触发词**: `优化初始化世界`

## 功能

在第一章发布前，将多轮 `审计原创性 -> 返工初始化世界` 收敛为一个 World Bible 质量优化闭环。该命令只围绕用户已选定题材打磨当前八类 World Bible，不自动回到 `热门话题`。

`热门话题` 可在选题阶段重复执行；一旦用户选定题材并进入 `初始化世界`，后续优化只处理当前题材。只有用户明确推翻题材，或连续全量审计仍为 `FAIL` 且确认底层机制不成立时，才回到 `热门话题`。

## 命令契约

- **输入**: 当前正式八类 World Bible、用户已选定题材、上一轮审计记录或用户补充要求。
- **前置条件**:
  - 八类 `world/*.md` 已由 `初始化世界` 创建。
  - `chapters/` 中不存在已发布 `CH-0001`。
  - 同一目标不存在进行中的初始化返工事务。
- **准备写入**: Agent 只写 `world/.staging/<transaction-id>/` 下的候选 World Bible、差异摘要、ID 映射和 YAML 证据。
- **正式写入范围**: 事务执行器只可替换八类 `world/*.md`。不得修改 `chapters/`、`metadata/`、正式 `world/archive/` 或选题报告。
- **确认要求**: 用户选择返工方向只授权生成候选版；覆盖正式 World Bible 前必须展示差异摘要并取得确认。
- **复审要求**: 每轮提交后必须新建全量 `审计原创性` 记录。该记录不作为本轮提交前置门禁；`PASS` 放行第一章，`WARN` 必须由用户重新接受，`FAIL` 继续优化或停止并报告底层机制风险。

## 执行流程

每轮优化执行以下闭环:

1. **全量审计**: 执行完整原创性审计，覆盖 A-K 维度和第一章前 L 维长篇展开性审计。
2. **方案选择**: 输出风险项、证据、验收条件和方案 A/B/自定义方向，等待用户选择或补充。
3. **候选生成**: 依据用户方向生成八类 World Bible 候选版，可重写 `outline.md`、人物、力量、地理、时间线、道具、叙事线索和章节摘要。
4. **差异预览**: 输出修改文件、核心设定变化、已解决风险、新增代价、不变硬约束、规划尺度变化和 ID 映射。
5. **用户确认**: 用户确认候选版后，写入覆盖确认和 `rework-user-approval` 语义证据。
6. **门禁提交**: 对 staging `outline.md` 运行 `python scripts/validate_outline.py <outline_file>`，并由事务执行器按正式目标基线替换八类 World Bible。
7. **全量复审**: 提交完成后新建只读 `审计原创性` 记录，不沿用上一轮 `WARN` 接受结论。

## 停止条件

- `PASS`: 可进入 `创作第 1 章`。
- `WARN`: 用户明确接受后可进入 `创作第 1 章`，复查点按 `audit-originality.md` 处理。
- `FAIL`: 不得进入第一章；继续优化，或由用户推翻当前题材并回到 `热门话题`。
- 用户满意但仍为 `FAIL`: 不得放行第一章。

## Subagent 边界

`gate-worker` 可作为可选内部证据员审查候选版是否满足原创性、长篇展开性、剧情逻辑、伏笔承诺和用户验收条件。它只返回结构化结论、证据定位、artifact 路径/hash、阻断风险和摘要；不得生成候选版、修改正式 World Bible、替用户接受 `WARN` 或执行事务提交。

## 相关规范

- [audit-originality.md](audit-originality.md)
- [rework-init-world.md](rework-init-world.md)
- [../originality-audit.md](../originality-audit.md)
- [../state-management.md](../state-management.md)
- [../chapter-creation-spec.md](../chapter-creation-spec.md)
