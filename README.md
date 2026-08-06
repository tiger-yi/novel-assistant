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

需要先查看方案但不写文件时使用：

```text
构思第 3 章
```

## 写作风格门禁

首次创作前必须显式执行一次 `创建写作风格`。生成的 `writespec/style-guide.md` 必须具有 `status: ready`，并包含核心调性、排版、受限视角、角色刻画、禁忌和黑名单。风格未就绪时，章节创作会停止而不会静默生成默认文风。

## 章节事务

章节事务分为两阶段：

1. **准备阶段**：在 staging 中完成正文、文本润色、最终门禁和 World Bible 变更预览，不修改正式章节或 World Bible。
2. **提交阶段**：发布正文、更新 World Bible、执行后置一致性校验，再按条件决定是否归档。

文本润色只处理语言、节奏、感官描写、物理化和去 AI 味。字数判断、内容补全、世界观审计和状态回写由外层事务负责。

## 归档行为

每满 10 章、卷结束或满足实体离场条件时触发归档判断。`创作第 N 章` 已包含一次条件授权：预览无歧义时自动归档；存在冲突或范围不清时只记录待处理，不会撤销已经通过后置校验的章节。

`归档世界` 仍可用于独立维护或重试待处理归档。

## 规范入口

| 范围 | 文件 |
| :--- | :--- |
| 主工作流 | [writespec/workflow.md](writespec/workflow.md) |
| 章节命令 | [writespec/commands/draft-chapter.md](writespec/commands/draft-chapter.md) |
| 章节流程 | [writespec/chapter-creation-spec.md](writespec/chapter-creation-spec.md) |
| 状态事务 | [writespec/state-management.md](writespec/state-management.md) |
| 文本润色 | [writespec/chapter-polish.md](writespec/chapter-polish.md) |
| 世界审计 | [writespec/world-audit.md](writespec/world-audit.md) |
| 归档规则 | [writespec/archiving-spec.md](writespec/archiving-spec.md) |

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
python -m unittest discover -s tests -v
```
