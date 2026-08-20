# Novel Assistant (AI 小说写作助手)

Novel Assistant 使用结构化 World Bible 管理中文玄幻长篇小说的剧情、人物、力量、时间、道具、地理、伏笔与章节摘要。Agent 从 [AGENTS.md](AGENTS.md) 进入，机器路由以 `novel-harness/context.manifest.yaml` 为准。

## 核心入口

日常只需要记住开书、日更和修复三类入口；完整命令仍由 Manifest 严格匹配。

| 场景 | 常用指令 |
| :--- | :--- |
| 开书 | `热门话题` -> `初始化世界` -> `优化初始化世界` -> `创建写作风格` |
| 日更 | `创作第 N 章` |
| 只看方案 | `构思第 N 章` |
| 修复状态 | `更新世界` / `归档世界` / `查看世界状态` / `清理事务缓存` |
| 修订规划 | `修订卷规划 ARC-001` |
| 正文等义优化 | `润色章节 CH-0001` / `润色当前章节` |
| 历史呈现迁移 | `迁移正文呈现` / `迁移正文呈现 CH-0001` |
| 发布准备 | `审计原创性` / `生成小说元数据` |

## 推荐流程

### 开书

```text
热门话题
初始化世界
优化初始化世界
创建写作风格
```

`热门话题` 是可选选题入口；已有题材时可直接从 `初始化世界` 开始。`优化初始化世界` 用于第一章前质量闭环，`返工初始化世界` 保留为底层修复命令，不作为日常推荐入口。

### 日更

```text
创作第 1 章
创作第 2 章
```

`创作第 N 章` 会绑定冻结的大纲修订、章节执行契约和 `INV-PAYOFF-001` 爽点兑现契约，生成一个不改变既定结果的执行方案，再完成撰写、文本润色、爽点证据校验、读者评价、验证、发布、更新 World Bible 和到期归档。规划缺失或过期、事实冲突、逻辑死锁、固定卷区间无法完成卷目标或爽点兑现失败时必须停止并按风险等级路由。

### 修复与高级维护

`更新世界` 和 `归档世界` 已包含在 `创作第 N 章` 的提交闭环内，只在恢复失败事务、补做状态回写或处理待归档项时单独使用。`清理事务缓存` 用于预览并确认删除保留期已满的本地 staging；它永久保留事务 YAML 与门禁证据，也不替代 World Bible 归档。`润色章节 CH-0001` 用于已发布正文的等义语言优化；`修订卷规划 ARC-001` 用于修改未发布卷规划；迁移、元数据和独立审计属于专项维护入口。

初始化时先确认全书卷路线图，再确认当前卷详细规划。全书路线图固定每卷章节闭区间、卷目标和卷间因果；当前卷在开卷前冻结全部里程碑与章节执行契约。后续卷必须先执行 `修订卷规划 ARC-001` 这类明确命令并取得覆盖确认，普通章节事务无权增章、重排或改写未来规划。每满十章的已发布详细规划可归档到 `world/archive/outline_history.md`，活跃大纲保留索引与 `archived_ranges`；归档前仍会校验活跃和历史契约合并后完整覆盖固定卷区间，并拒绝隐藏未发布章节。

`热门话题` 可重复执行；用户不满意候选题材、想换平台、受众、时间窗或题材边界时可重跑。一旦用户选定题材并进入 `初始化世界`，热门话题退出当前闭环；后续 `优化初始化世界` 只围绕已选题材打磨 World Bible。只有用户明确推翻题材，或连续返工仍 `FAIL` 且确认底层机制不成立时，才回到 `热门话题`。

初始化完成后、第一章发布前，推荐使用 `优化初始化世界` 执行质量闭环：全量 `审计原创性`、用户选择返工方向、生成 World Bible 候选版、展示差异摘要、用户确认提交、执行器替换正式八类文件，再次全量复审。该闭环必须检查故事力基线：主角主动目标、主题透镜、有效冲突、情理内反转、角色功能和黄金三章牵引。`PASS` 可进入第一章；`WARN` 需要用户重新接受后放行，并只在 `CH-0010` 或 `ARC-001` 卷终二者较早处复查一次；`FAIL` 阻断第一章。`返工初始化世界` 保留为单轮底层命令；用户选择方案不等于确认覆盖，正式替换前必须看候选差异摘要。

命令由 `python scripts/novel_harness.py resolve "<原始指令>"` 严格匹配。写命令先通过 `begin` 创建 YAML 事务，Agent 只准备 staging 内容；正式章节、World Bible、归档、风格和报告由事务执行器校验基线与门禁后提交。`审计原创性` 也创建只读执行记录，用于证明每 10 章周期门禁已经生效。Windows 控制台传中文参数不稳定时，可把原始指令保存为 UTF-8 文件，并使用 `--text-file <command.txt>`；也可用 `--text-stdin` 从 UTF-8 stdin 读取。

八类 World Bible 初始化模板用于 `初始化世界`、第一章前 `返工初始化世界` / `优化初始化世界` 候选和修复缺失文件；章节后回写和 `更新世界` 依据 `writespec/world-bible-contract.md`、当前 `world/*.md`、正文证据和事务变更集执行。

覆盖已有风格、元数据或初始化目标时，用户需运行 `python scripts/novel_harness.py confirm-overwrite <transaction.yaml> <target>` 并按提示输入精确目标；直接编辑 YAML 不会形成有效确认。

需要先查看方案但不写文件时使用：

```text
构思第 3 章
```

## 写作风格门禁

首次创作前，`writespec/style-guide.md` 必须满足 `INV-STYLE-001`。推荐通过 `创建写作风格` 生成；人工编辑或迁移的文件只要通过同一结果门禁也可使用。完整章节创作会校验 `style_basis` 书名锚点，缺字段或与 `world/outline.md` 书名不匹配时停止，不会静默生成默认文风。创建风格时若用户未确认文风候选，候选只能保持 `draft`；设为 `ready` 前还必须完成 `longform-style-readiness` 语义门禁、长篇适配证据和错误/修正示例。后续每章还必须通过 `style-application` 语义门禁，证明正文实际应用当前风格指南。

## 章节事务

章节事务分为两阶段：

1. **准备阶段**：在 staging 中完成正文、文本润色、最终门禁和 World Bible 候选文件，不修改正式章节或 World Bible。
2. **提交阶段**：事务执行器校验 YAML 证据与目标基线，发布正文、更新 World Bible、执行后置一致性校验，再按条件决定是否归档。

文本润色只处理语言、节奏、感官描写、物理化和去 AI 味。读者评价只用于新章 staging 正文的多读者画像评分和受限重润色建议，不写入正式 World Bible。字数判断、内容补全、世界观审计和状态回写由外层事务负责。

已发布章节需要多次语言优化时使用 `润色章节 CH-0001`，且始终保持等义呈现。若已发布章节需要结构性重创，继续使用 `创作第 N 章`；执行器检测目标已发布后进入 `published-revision` 条件模式，生成新 `RNN`、爽点与下游影响预览，并在明确批准后提交。若只想处理当前活跃章节事务内的 staging，使用 `润色当前章节`；找不到活跃 staging 时返回 `STAGING_NOT_FOUND`。

Manifest 支持可选 subagent delegation 策略。subagent 可以全量读取仓库，但只作为 evidence artifact 生产者，返回结构化结论、证据路径和 hash；正式章节、World Bible、归档和摘要索引仍只能由事务执行器提交。

`构思第 N 章` 和 `创作第 N 章` 都必须输出六维世界观风险表，覆盖体系、战力、时间、物品、地理和人物行为。战力项必须给出境界差距、既有依据、正文代价和 `INV-POWER-001` 结论；熔断项不能靠事后修改 World Bible 放行。

新章节标题必须与已发布章节、当前活动 staging 和章节摘要中的既有标题不重名；`构思第 N 章` 也要给出候选标题的唯一性结论。

悬念钩子使用 `HOOK-*`，伏笔使用 `SEED-*`。两者保存在同一个 `world/hooks.md` 注册表中，但采用独立生命周期；只有已发布正文提供证据后，候选才能进入正式状态。

`构思第 N 章` 和 `创作第 N 章` 都必须输出叙事线索处理表，说明本章如何处理活跃钩子、伏笔、到期线索和新候选线索。候选只在构思阶段存在；发布前必须用正文证据生成变更集，才允许写入 `world/hooks.md`。

每章都必须具有服务主线的“章末牵引”，但只有需要跨章追踪的问题或承诺才登记为 `HOOK-*`。剧情对齐是阻断门禁；留存质量可以重写优化，但不能成为偏离卷目标、临时增加支线或新增重大设定的理由。

爽点不是钩子或伏笔。新初始化/修订大纲在 `outline.md` 规划爽点契约，每次后续章节事务在 staging 生成 `payoff-evidence.yaml`，先由 `python scripts/validate_payoff.py` 校验结构和滚动密度，再由语义门禁核对正文中的行动、状态变化、确认与代价。旧章节和未声明启用策略的旧冻结契约不追溯失败。

`INV-CHAPTER-001` 同时禁止面板化符号、书名号、内部 ID、裸字母数字代号、章节结构引用、非对话引号和叙事层泄漏。章节创作、两种正文润色与历史呈现迁移都通过必需的 `narrative-integrity` 提交 `reported_speech_audit`；旧话转述的表达选择以 `writespec/chapter-creation-spec.md` 为唯一正式指导。使用 `python scripts/novel_harness.py invariants` 可从 Manifest 动态查看全部 INV 的唯一 owner 与相关门禁；项目不维护重复的 `INV/` 目录。

历史正文通过 `迁移正文呈现` 先执行只读扫描，再对授权清单逐章使用 `迁移正文呈现 CH-NNNN`。每章生成新的 `RNN`，只允许等义修改呈现和证据指针；剧情事实、实体状态和线索生命周期不得变化。单章失败不回滚其他已完成章节，父批次保留 `PARTIAL` 状态和恢复范围。

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
| 初始化优化 | [writespec/commands/optimize-init-world.md](writespec/commands/optimize-init-world.md) |
| 初始化返工 | [writespec/commands/rework-init-world.md](writespec/commands/rework-init-world.md) |
| 原创性审计 | [writespec/originality-audit.md](writespec/originality-audit.md) |
| 润色命令 | [writespec/commands/polish-chapter.md](writespec/commands/polish-chapter.md) |
| 章节流程 | [writespec/chapter-creation-spec.md](writespec/chapter-creation-spec.md) |
| 读者评价（含高分证据校验） | [writespec/reader-evaluation.md](writespec/reader-evaluation.md) |
| 卷规划修订 | [writespec/commands/revise-arc.md](writespec/commands/revise-arc.md) |
| 叙事线索 | [writespec/foreshadowing-spec.md](writespec/foreshadowing-spec.md) |
| 状态事务 | [writespec/state-management.md](writespec/state-management.md) |
| World Bible 运行期契约 | [writespec/world-bible-contract.md](writespec/world-bible-contract.md) |
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
python scripts/novel_harness.py invariants
python scripts/validate_outline.py <outline_file>
python scripts/check_count.py <chapter_file> --target 2300 --max 2800 --segments
python scripts/validate_chapter.py <chapter_file> --target 2300 --max 2800
python scripts/novel_harness.py resolve "创作第 1 章"
python scripts/novel_harness.py resolve --text-file <utf8-command-file>
python scripts/novel_harness.py resolve "优化初始化世界"
python scripts/render_workflow.py create-chapter
python -m unittest discover -s tests -v
```
