---
schema: novel-harness/agents/v1
primary_home: novel-harness
---

# AGENTS.md - Novel Assistant

## Project Snapshot

Novel Assistant 是中文玄幻长篇小说的结构化创作 Harness。项目以八类 World Bible 维护剧情、人物、力量、时间、道具、地理、伏笔和章节摘要，采用大纲驱动的章节事务。

默认闭环为：**风格就绪 -> 构思与撰写 -> 润色与验证 -> 准备变更集 -> 发布并更新世界 -> 后置校验 -> 条件归档**。

## 规范索引

`novel-harness/context.manifest.yaml` 是路由、加载顺序和验证命令的机器唯一事实来源。本文件是 Agent 人工入口，不再维护 Manifest 的完整镜像。

| 需要 | 文件 |
| :--- | :--- |
| 主工作流 | `novel-harness/context.manifest.yaml` 的 `pipelines` 段 |
| 章节协议 | `writespec/commands/draft-chapter.md`, `writespec/chapter-creation-spec.md` |
| 叙事线索 | `writespec/foreshadowing-spec.md` |
| 状态与事务 | `writespec/state-management.md` |
| World Bible 运行期契约 | `writespec/world-bible-contract.md` |
| 文本润色 | `writespec/chapter-polish.md` |
| 风格与物理化 | `writespec/style-guide.md`, `writespec/chapter-polish.md` |
| 世界观审计 | `writespec/world-audit.md` |
| 归档 | `writespec/commands/archive-world.md`, `writespec/archiving-spec.md` |
| 原创性审计 | `writespec/originality-audit.md`, `writespec/trope-blacklist.md` |
| 元数据 | `writespec/metadata-guide.md` |
| 架构决策 | `novel-harness/adr/` |
| 受控改进 | `writespec/continuous-improvement.md`, `novel-harness/improvement-log.md` |
| 校验脚本 | `scripts/check_count.py`, `scripts/validate_chapter.py`, `scripts/validate_harness.py` |

## Agent Working Rules

- 动手前陈述已加载上下文、假设、影响范围和验证方案。
- 优先采用满足需求的最简方案，只修改必要文件。
- 以实际文件、命令结果和生成证据为准。
- 不得要求或输出完整内部推理链；只报告决策摘要、文件证据和风险。
- 自我提升只允许按 `continuous-improvement.md` 生成 `IMP-*` 提案；未经证据验证和用户批准，不得自动修改正式规则。
- 声称完成前必须执行相关确定性验证。

## Startup Order

非平凡任务按以下顺序加载：

1. 读取本文件。
2. 读取 `novel-harness/context.manifest.yaml`。
3. 按命令路由读取 `writespec/commands/*.md`。
4. 按需读取规范与模板。
5. 构思或创作前按任务模式加载 `world_data.profiles`；无匹配项才使用默认顺序。
6. 命中归档索引、历史实体或跨卷因果时，按 `state-management.md` 最小回溯。

小任务可只加载相关子集，但必须说明范围和假设。

## Core Commands

| 命令入口 | 协议文件 |
| :--- | :--- |
| `初始化世界` | `writespec/commands/init-world.md` |
| `返工初始化世界` | `writespec/commands/rework-init-world.md` |
| `创建写作风格` | `writespec/commands/create-style.md` |
| `创作章节`：`创作第 N 章` / `构思第 N 章` | `writespec/commands/draft-chapter.md` |
| `修订卷规划 ARC-001` | `writespec/commands/revise-arc.md` |
| `迁移正文呈现` / `迁移正文呈现 CH-0001` | `writespec/commands/migrate-presentation.md` |
| `润色章节 CH-0001` / `润色当前章节` | `writespec/commands/polish-chapter.md` |
| `更新世界` | `writespec/commands/update-world.md` |
| `归档世界` | `writespec/commands/archive-world.md` |
| `查看世界状态` | `writespec/commands/check-status.md` |
| `热门话题` | `writespec/commands/trending.md` |
| `审计原创性` | `writespec/commands/audit-originality.md` |
| `生成小说元数据` | `writespec/commands/generate-metadata.md` |

本表仅用于人工导航；触发词、别名和匹配模式以 Manifest 为准。

## Source Priority And Authority

- 当前任务的直接用户指令优先于普通项目指引。
- `writespec/` 定义项目语义协议。
- `novel-harness/context.manifest.yaml` 定义机器路由、加载顺序和门禁。
- `INV-<DOMAIN>-NNN` 在所属权威规范中定义；其他文件只引用稳定 ID，不复制规则正文。
- `IMP-*` 仅是非约束性的改进提案，不得作为命令协议、门禁或小说事实执行。
- 小说事实冲突以 `writespec/state-management.md` 为准，必须停止自动覆盖并报告证据。
- 已有历史偏差不构成引入新偏差的许可。

## Prohibitions

- 禁止绕过必需门禁，或仅凭 Agent 自审替代确定性脚本与语义证据。
- 禁止提交 secrets、token 或生产数据。

## Write Boundaries

写入范围、暂停条件、事务阶段和归档授权以对应命令协议及 `writespec/state-management.md` 为准，不得从命令名称推断额外写入权限。

原始命令必须由 `scripts/novel_harness.py` 按 Manifest 严格解析。Agent 只写命令授权的 staging 与 YAML 证据；正式章节、World Bible、归档、风格和报告目标只能由事务执行器提交。

## When You Change X, Also Check Y

- 修改命令协议时，同步更新 Manifest、README 和对应规范。
- 修改卷路线图、章节执行契约或剧情对齐规则时，同步更新大纲模板、章节规范、世界审计、事务绑定校验和测试。
- 修改正文呈现边界、历史正文迁移或正式正文润色规则时，同步更新章节规范、风格指南、正文校验器、迁移/润色命令、事务测试和 Manifest 门禁。
- 新增规范、模板或技能时，只更新 Manifest 路由和 AGENTS 简要入口；不创建重复的完整索引镜像。
- 修改风格就绪结构时，同步更新 `create-style.md`、Harness 校验器和测试。
- 修改 World Bible 初始化字段时，同步更新模板和 `world-audit.md`；修改运行期字段、动作或证据时，同步更新 `world-bible-contract.md`、`world-audit.md`、状态管理和 Manifest 门禁。
- 修改初始化返工、第一章前原创性放行或长篇展开性审计时，同步更新 `audit-originality.md`、`originality-audit.md`、`rework-init-world.md`、Manifest 路由和 README。
- 修改悬念钩子或伏笔字段、状态或证据规则时，同步更新 `foreshadowing-spec.md`、模板、状态管理、世界审计与归档规范。
- 修改事务或归档规则时，同步更新状态规范、YAML 事务记录模板和归档规范。
- 修改校验脚本时，同步更新 `tests/` 与 Manifest 验证命令。
- 修改 INV 时检查唯一权威、Manifest 所有者和验证覆盖；改变 ADR 决策时新增替代 ADR，不重写历史理由。

## Verification Gates

完成前必须执行 Manifest 路由的相关确定性门禁，并按对应规范提供语义证据；任何必需门禁失败均不得静默跳过或声称完成。

## Completion And Failure

- 必需变更完成且影响范围受控。
- 相关验证已经执行并报告结果。
- 失败时报告命令、证据、最后成功步骤和恢复点。
- 不得自动覆盖或整文件回滚用户已有差异。
