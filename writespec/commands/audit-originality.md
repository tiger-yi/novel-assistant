# 命令协议: 审计原创性 (audit-originality)

## 功能

`审计原创性` 显式执行完整长篇原创性审计，与周期门禁及 `热门话题` 复用同一个 `audit-originality` pipeline。

## 命令契约

- **生效入口**: `command`
- **副作用**: 只读；默认只输出结构化审计报告。
- **输入**: 当前大纲、人物、力量、地理、章节摘要与相关正文证据。
- **禁止写入**: 不得直接修改 World Bible、已发布章节或正式元数据。
- **执行记录**: 通过 `begin` 创建只读 YAML 事务记录；不创建正式内容变更集，完成后由执行器校验语义证据并记录 `coverage.through_chapter` 与 `coverage.events`。

## 执行流程

1. 按 Manifest 加载 `audit-originality` pipeline 与 `full-audit` World Data profile。
2. 按 `originality-audit.md` 完成全部维度审计，并引用文件、章节 ID 或实体 ID。
3. 门禁结果统一使用 `PASS`、`WARN`、`FAIL` 或附原因的 `NOT_APPLICABLE`。
4. 优化建议只作为候选；需要修改 World Bible 时必须另行取得写命令授权并创建事务。
5. 每 10 章周期门禁及 `outline_initialized`、`arc_completed`、`premise_changed` 事件，以状态为 `COMPLETE` 且覆盖相应章节边界/事件事务 ID 的本命令记录为准；缺失时下一章不得开始。

用于解除周期阻断的 `audit` 门禁必须为带语义证据的 `PASS` 或 `WARN`；`NOT_APPLICABLE` 记录不能提供周期覆盖。

## 相关规范

- [../originality-audit.md](../originality-audit.md)
- [../trope-blacklist.md](../trope-blacklist.md)
