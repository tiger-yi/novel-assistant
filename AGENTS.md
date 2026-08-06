---
schema: novel-harness/agents/v1
primary_home: novel-harness
---

# AGENTS.md - Novel Assistant

## Project Snapshot

Novel Assistant 是中文玄幻长篇小说的结构化创作 Harness。项目以八类 World Bible 维护剧情、人物、力量、时间、道具、地理、伏笔和章节摘要，采用大纲驱动的章节事务。

默认闭环为：**风格就绪 -> 构思 -> 撰写 -> 文本润色 -> 验证 -> 两阶段提交 -> 更新世界 -> 条件归档**。

## 规范索引

`novel-harness/context.manifest.yaml` 是路由、加载顺序和验证命令的机器唯一事实来源。本文件是 Agent 人工入口，不再维护 Manifest 的完整镜像。

| 需要 | 文件 |
| :--- | :--- |
| 主工作流 | `writespec/workflow.md` |
| 章节协议 | `writespec/commands/draft-chapter.md`, `writespec/chapter-creation-spec.md` |
| 状态与事务 | `writespec/state-management.md` |
| 文本润色 | `writespec/chapter-polish.md` |
| 风格与物理化 | `writespec/style-guide.md`, `writespec/physical-descriptor.md` |
| 世界观审计 | `writespec/world-audit.md` |
| 归档 | `writespec/commands/archive-world.md`, `writespec/archiving-spec.md` |
| 原创性审计 | `writespec/originality-audit.md`, `writespec/audit-dimensions.md`, `writespec/trope-blacklist.md`, `writespec/original-check-guide.md` |
| 元数据 | `writespec/metadata-guide.md`, `writespec/platform-rules.md`, `writespec/tag-options.md` |
| 校验脚本 | `scripts/check_count.py`, `scripts/validate_chapter.py`, `scripts/validate_harness.py` |

## Agent Working Rules

- 动手前陈述已加载上下文、假设、影响范围和验证方案。
- 优先采用满足需求的最简方案，只修改必要文件。
- 以实际文件、命令结果和生成证据为准。
- 不得要求或输出完整内部推理链；只报告决策摘要、文件证据和风险。
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

| 命令 | 触发词 | 协议文件 |
| :--- | :--- | :--- |
| 初始化世界 | `初始化世界` | `writespec/commands/init-world.md` |
| 创建写作风格 | `创建写作风格` | `writespec/commands/create-style.md` |
| 创作章节 | `创作第 N 章` | `writespec/commands/draft-chapter.md` |
| 只读构思 | `构思第 N 章` | `writespec/commands/draft-chapter.md` |
| 更新世界 | `更新世界` | `writespec/commands/update-world.md` |
| 归档世界 | `归档世界` | `writespec/commands/archive-world.md` |
| 查看世界状态 | `查看世界状态` | `writespec/commands/check-status.md` |
| 热门话题 | `热门话题` | `writespec/commands/trending.md` |

## Source Priority And Authority

- 当前任务的直接用户指令优先于普通项目指引。
- `writespec/` 定义项目语义协议。
- `novel-harness/context.manifest.yaml` 定义机器路由、加载顺序和门禁。
- 小说事实冲突以 `writespec/state-management.md` 为准，必须停止自动覆盖并报告证据。
- 已有历史偏差不构成引入新偏差的许可。

## Prohibitions

- 禁止绕过 World Bible 六维审计和逻辑闭环。
- 正文严禁 `【 】`、`[ ]`、`（ ）`、Markdown 列表/表格和加粗。
- 非对话严禁使用引号。
- 禁止越 2 大境界取胜、天降名词、无来源道具和无代价越级。
- 禁止仅凭 Agent 自审替代确定性脚本。
- 禁止提交 secrets、token 或生产数据。

## Write Boundaries

- `构思第 N 章` 只输出预演，不写文件。
- `创作第 N 章` 自动采用推荐分支并进入完整事务；仅在事实冲突、逻辑死锁或修订已发布章节时暂停。
- 首次创作前必须显式执行一次 `创建写作风格`；风格未达到 `status: ready` 时熔断。
- 文本润色只修改 staging 正文，不负责补字数、审计、回写或归档。
- 准备阶段不修改正式章节或 World Bible；提交阶段才发布并应用已准备的变更集。
- `创作第 N 章` 包含一次条件归档授权：到期且无歧义时自动归档，有歧义时标记待处理。
- `更新世界` 和 `归档世界` 保留为独立修复、恢复或人工维护入口。

## When You Change X, Also Check Y

- 修改命令协议时，同步更新 Manifest、README 和对应规范。
- 新增规范、模板或技能时，只更新 Manifest 路由和 AGENTS 简要入口；不创建重复的完整索引镜像。
- 修改风格就绪结构时，同步更新 `create-style.md`、Harness 校验器和测试。
- 修改 World Bible 字段时，同步更新模板和 `world-audit.md`。
- 修改事务或归档规则时，同步更新状态规范、事务日志模板和归档规范。
- 修改校验脚本时，同步更新 `tests/` 与 Manifest 验证命令。

## Verification Gates

未跑完相关门禁不得声称任务完成：

- **风格就绪**：`python scripts/validate_harness.py` 校验 `status: ready` 和风格必需章节。
- **构思门**：推荐分支的承接、消耗、战力、时空、人物和信息差审计无 ❌。
- **章节字数**：`python scripts/check_count.py <章节文件> --target 2000 --segments`。
- **章节格式**：`python scripts/validate_chapter.py <章节文件> --target 2000`。
- **六维语义**：按 `world-audit.md` 记录带文件、章节 ID 或实体 ID 的结果。
- **准备提交**：World Bible 变更集无事实冲突，字段动作和幂等键齐全。
- **事务后置**：正式正文与已验证版本一致，World Bible 引用、消耗、伤势、信息差和事务状态闭环。
- **周期原创性**：初始化后、每 10 章、卷结束或核心设定变更时执行完整审计；阻断项未解决不得进入下一周期。
- **条件归档**：到期且无歧义时自动执行；歧义必须记录为待处理。

自动修正正文最多 3 轮。门禁失败时报告冲突点，不得静默跳过。

## Definition of Done

- 必需文件变更已完成。
- 相关验证命令已执行并报告结果。
- 完整章节事务包含事务 ID、推荐分支、正式章节、World Bible 变更、门禁证据和归档子状态。
- 准备阶段失败时没有正式写入；提交阶段失败时记录最后成功步骤与恢复点。
- 归档歧义可作为待处理子状态，但不得伪装为归档成功。

## Failure Handling

- 本次改动引发的验证失败必须修复后再声称完成。
- 存量失败需附命令和证据单独报告。
- 缺环境或凭据时报告确切缺失项。
- 禁止自动整文件回滚用户已有差异。
