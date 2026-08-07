# Novel Assistant (AI 小说写作助手)

Novel Assistant 使用结构化 World Bible 管理中文玄幻长篇小说的剧情、人物、力量、时间、道具、地理、伏笔与章节摘要。Agent 从 [AGENTS.md](AGENTS.md) 进入，机器路由以 `novel-harness/context.manifest.yaml` 为准。

## 核心指令

| 目的 | 指令 |
| :--- | :--- |
| 初始化八类 World Bible | `初始化世界` |
| 一次性定制全书文风 | `创建写作风格` |
| 创作章节并自动收尾 | `创作第 N 章` |
| 仅查看细纲与推荐分支 | `构思第 N 章` |
| 独立修复状态回写 | `更新世界` |
| 独立执行归档维护 | `归档世界` |
| 查看当前世界状态 | `查看世界状态` |
| 分析热门题材 | `热门话题` |
| 执行完整原创性审计 | `审计原创性` |
| 生成发布元数据方案 | `生成小说元数据` |

## 推荐流程

新项目只需先执行：

```text
初始化世界
创建写作风格
```

随后每章只需一条指令：

```text
创作第 1 章
创作第 2 章
```

`创作第 N 章` 会自动完成构思、采用推荐分支、撰写、文本润色、必要的内容补全、验证、发布、更新 World Bible 和到期归档。只有事实冲突、逻辑死锁或修订已发布章节时才暂停。

命令由 `python scripts/novel_harness.py resolve "<原始指令>"` 严格匹配。写命令先通过 `begin` 创建 YAML 事务，Agent 只准备 staging 内容；正式章节、World Bible、归档、风格和报告由事务执行器校验基线与门禁后提交。`审计原创性` 也创建只读执行记录，用于证明每 10 章周期门禁已经生效。

覆盖已有风格、元数据或初始化目标时，用户需运行 `python scripts/novel_harness.py confirm-overwrite <transaction.yaml> <target>` 并按提示输入精确目标；直接编辑 YAML 不会形成有效确认。

需要先查看方案但不写文件时使用：

```text
构思第 3 章
```

## 写作风格门禁

首次创作前，`writespec/style-guide.md` 必须满足 `INV-STYLE-001`。推荐通过 `创建写作风格` 生成；人工编辑或迁移的文件只要通过同一结果门禁也可使用。风格未就绪时，章节创作会停止而不会静默生成默认文风。

## 章节事务

章节事务分为两阶段：

1. **准备阶段**：在 staging 中完成正文、文本润色、最终门禁和 World Bible 候选文件，不修改正式章节或 World Bible。
2. **提交阶段**：事务执行器校验 YAML 证据与目标基线，发布正文、更新 World Bible、执行后置一致性校验，再按条件决定是否归档。

文本润色只处理语言、节奏、感官描写、物理化和去 AI 味。字数判断、内容补全、世界观审计和状态回写由外层事务负责。

悬念钩子使用 `HOOK-*`，伏笔使用 `SEED-*`。两者保存在同一个 `world/hooks.md` 注册表中，但采用独立生命周期；只有已发布正文提供证据后，候选才能进入正式状态。

## 归档行为

每满 10 章、卷结束或满足实体离场条件时触发归档判断。开始第 11、21 等下一周期章节前，还必须存在覆盖上一章节边界的已完成原创性审计记录。`创作第 N 章` 已包含一次条件归档授权：预览无歧义时自动归档；存在冲突或范围不清时只记录待处理，不会撤销已经通过后置校验的章节。

`归档世界` 仍可用于独立维护或重试待处理归档。

## 受控改进

Agent 只在重复失败、人工纠正、门禁冲突或事务恢复暴露规则缺口时生成 `IMP-*` 改进提案。提案不具备规则效力，必须经过证据验证和用户批准，才能晋升为普通规范、INV 或 ADR。

## 规范入口

AGENTS 只提供人工入口和跨项目原则；Manifest 管理机器路由、加载顺序与验证命令；命令协议和专项规范定义行为语义与 INV；本 README 只提供用户操作说明。

| 范围 | 文件 |
| :--- | :--- |
| 主工作流 | `python scripts/render_workflow.py create-chapter` |
| 章节命令 | [writespec/commands/draft-chapter.md](writespec/commands/draft-chapter.md) |
| 章节流程 | [writespec/chapter-creation-spec.md](writespec/chapter-creation-spec.md) |
| 叙事线索 | [writespec/foreshadowing-spec.md](writespec/foreshadowing-spec.md) |
| 状态事务 | [writespec/state-management.md](writespec/state-management.md) |
| 文本润色 | [writespec/chapter-polish.md](writespec/chapter-polish.md) |
| 世界审计 | [writespec/world-audit.md](writespec/world-audit.md) |
| 归档规则 | [writespec/archiving-spec.md](writespec/archiving-spec.md) |
| 受控改进 | [writespec/continuous-improvement.md](writespec/continuous-improvement.md) |

## 开发与验证

安装依赖：

```powershell
python -m pip install -r requirements-dev.txt
```

运行门禁：

```powershell
python scripts/validate_harness.py
python scripts/check_count.py <chapter_file> --target 2000 --segments
python scripts/validate_chapter.py <chapter_file> --target 2000
python scripts/novel_harness.py resolve "创作第 1 章"
python scripts/render_workflow.py create-chapter
python -m unittest discover -s tests -v
```
