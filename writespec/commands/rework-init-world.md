# 命令协议: 返工初始化世界 (rework-init-world)

**触发词**: `返工初始化世界`

## 功能

在第一章发布前, 基于一次 `审计原创性` 记录和用户选择的返工要求, 生成新的八类 World Bible 返工候选版。用户确认候选预览后, 由事务执行器替换正式八类 `world/*.md`。

本命令只解决初始化后不满意的世界观返工。第一章发布后不得使用本命令。

## 术语

- **返工候选版**: 第一章前某轮 World Bible 候选或废弃版本, 只存在于事务记录或 staging 中, 不进入正式 `world/archive/`。
- **世界历史归档**: 发布正文后由事实演化产生的历史状态, 才允许进入 `world/archive/`。

## 命令契约

- **输入**: 指定 `审计原创性` 事务记录、用户选择的方案 A/B 或补充要求、当前正式八类 World Bible。
- **前置条件**:
  - 八类 `world/*.md` 已由 `初始化世界` 创建。
  - `chapters/` 中不存在已发布 `CH-0001`。
  - 指定审计记录状态为 `COMPLETE`, 且包含风险项、返工验收条件和长篇展开性审计结论。
  - 同一目标不存在进行中的初始化返工事务。
- **准备写入**: Agent 只写 `world/.staging/<transaction-id>/` 下的八类返工候选版、差异摘要、ID 映射和 YAML 证据。
- **正式写入范围**: 事务执行器只可替换八类 `world/*.md`。不得修改 `writespec/`、`templates/`、`chapters/`、`metadata/` 或正式 `world/archive/`。
- **确认要求**: 候选预览必须经用户确认后才能提交。覆盖正式八类 `world/*.md` 仍需按 Manifest 的覆盖确认执行。
- **复审要求**: 提交后必须自动执行 `审计原创性` 复审。复审 `PASS` 放行第一章；`WARN` 必须重新取得用户接受；`FAIL` 阻断第一章并要求继续返工。

## 执行流程

1. **前置扫描**: 确认 `CH-0001` 未发布、八类 World Bible 齐全、审计事务存在且完成。
2. **读取审计基线**: 提取风险项、方案 A/B、返工验收条件、长篇展开性审计结论和短期复查要求。
3. **生成返工候选版**: 可重写全部八类 World Bible, 包括 `outline.md`、人物、力量、地理、时间线、道具、叙事线索和章节摘要。
4. **候选预览**: 输出与当前正式 World Bible 的差异摘要, 至少包含:
   - 被修改文件。
   - 核心设定变化。
   - 被解决的审计风险项。
   - 新增风险或代价。
   - 不变的硬约束。
   - 规划尺度变化: 全书卷数、章节区间、总字数目标、卷目标和里程碑变化。
   - ID 映射: 旧 ID、旧名称、新 ID、新名称、重建原因、影响文件。
5. **用户确认**: 用户确认采用候选版后, 写入覆盖确认和 `rework-user-approval` 语义证据。
6. **门禁**:
   - 对 staging `outline.md` 运行 `python scripts/validate_outline.py <outline_file>`。
   - 按 `originality-audit.md` 对候选版执行长篇展开性审计。
7. **提交**: 事务执行器按八类 World Bible 目标基线和变更集替换正式文件。废弃候选版只保留在事务记录或 staging, 不进入 `world/archive/`。
8. **自动复审**: 新建只读 `审计原创性` 记录。`WARN` 不能沿用上一轮接受, 必须重新确认。

## ID 与规划尺度

第一章前允许重建 `CHAR-*`、`LOC-*`、`FAC-*`、`ITEM-*`、`HOOK-*`、`SEED-*` 和 `EVT-*`, 但必须在差异摘要中列出映射。第一章发布后, 稳定 ID 不得因改名、状态变化或展示名称变化而改变。

第一章前允许改变全书卷数、章节区间和总字数目标, 但必须重新通过 `outline-contract`, 并在差异摘要中单列规划尺度变化。

## WARN 处理

第一章前长篇展开性审计:

- `PASS`: 可进入 `创作第 1 章`。
- `WARN`: 用户可接受后放行, 但只保留到最近一个明确复查点。
- `FAIL`: 阻断, 必须继续返工。

被接受的 `WARN` 只短期复查一次。复查点为 `CH-0010` 或 `ARC-001` 卷终, 二者取更早。复查结果为:

- 已缓解: 关闭。
- 未恶化: 关闭, 视为作者取舍。
- 已恶化: 升级为新一轮 `WARN` 或 `FAIL`。

不得把第一章前接受的 `WARN` 长期追踪到后续远期章节。

## 相关规范

- [audit-originality.md](audit-originality.md)
- [../originality-audit.md](../originality-audit.md)
- [../state-management.md](../state-management.md)
- [../world-bible-contract.md](../world-bible-contract.md)
- [../chapter-creation-spec.md](../chapter-creation-spec.md)
