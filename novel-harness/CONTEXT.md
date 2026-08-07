# Novel Assistant — 创作 Harness 域词汇表

本上下文描述 Novel Assistant 的 Agent 创作工作台 (harness) 领域: 命令协议、规范地图、World Bible 与创作闭环中使用的核心术语。

## Language

**World Bible**:
项目核心的结构化世界观数据文件集合 (`world/*.md`), 由 outline/characters/power/timeline/inventory/geography/hooks/chapter-summary 组成, 是当前规范化状态的事实来源；已发生事件以发布章节为证据，冲突按 `state-management.md` 处理。
_Avoid_: 设定文件、数据文件 (过泛)

**World Bible 运行期结构契约**:
`writespec/world-bible-contract.md`, 定义八类 World Bible 在章节事务与 `更新世界` 中的字段、动作、证据和幂等要求；不同于初始化模板，不承载示例剧情或创作问卷。
_Avoid_: 模板、初始化蓝图

**命令协议 (Command Protocol)**:
每个核心指令 (初始化世界/更新世界/...) 对应的独立执行规范文件, 存放于 `writespec/commands/*.md`, 定义触发词、功能与执行流程。
_Avoid_: 命令文档、指令说明

**命令解析 (Command Resolution)**:
事务执行器依据 Manifest 的精确触发词、别名或正则模式匹配原始用户指令，并据此授予对应读写权限；Agent 不得临时推断未注册的写命令。
_Avoid_: 意图猜测、自然语言自动授权

**context.manifest.yaml**:
novel-harness 的机器可读执行清单, 是命令路由、执行阶段、规范加载顺序、世界数据加载顺序与验证命令的唯一事实来源。
_Avoid_: 配置文件、地图文件 (语境重叠时)

**人工入口 (Human Entry)**:
`AGENTS.md`, 面向 Agent 说明跨项目原则与规范入口, 不承载命令流程、门禁阈值或领域规则正文。
_Avoid_: 总规范、完整规范镜像

**不变量 (Invariant, INV)**:
违反即阻断流程的稳定领域规则, 使用 `INV-<DOMAIN>-NNN` 标识并只在所属权威规范中定义, 其他文件仅引用其 ID。
_Avoid_: 检查项、规则副本、验收清单

**受控改进 (Controlled Improvement)**:
Agent 从重复失败、人工纠正或恢复证据中生成非约束性提案，经验证和人工批准后才允许晋升为正式规则的改进闭环。
_Avoid_: 自我学习、自我进化 (暗示未经授权自动改写规则)

**改进提案 (Improvement Proposal)**:
使用 `IMP-NNNN` 标识的问题、证据与建议记录；在晋升前不具备规则效力。
_Avoid_: 新规则、经验规则

**加载顺序 (Loading Order)**:
执行任务前读取上下文与 World Bible 的既定先后次序, 由 manifest 的 `loading_policy` 与 `world_data.default_order` 定义。
_Avoid_: 读取流程、初始化步骤

**生效入口 (Activation Type)**:
Manifest 为每个规范声明的唯一主调用方式，限定为 `command`、`pipeline`、`event`、`periodic`、`profile` 或 `reference`；未声明的规范不可执行。
_Avoid_: 按需生效、Agent 自行发现

**五步登仙 (Five-Step Genesis)**:
初始化世界时引导用户从五个维度 (流派/金手指/开局/世界观/情感) 通过多选构建世界观基石的交互协议, 现扁化并入 `init-world.md`。
_Avoid_: 创建向导、初始化引导

**ReAct 工作流**:
章节创作采用决策摘要-行动-观察循环，由 `chapter-creation-spec.md` 定义构思、初稿与最终门禁；对外只保留文件依据、关键约束和风险。
_Avoid_: 创作流程 (过泛)

**创作指令 (Create Chapter Command)**:
`创作第 N 章`，绑定冻结章节执行契约并完成准备、提交、状态回写和条件归档的一次完整章节事务。
_Avoid_: 撰写章节、构思并写作、写第 N 章

**卷契约 (Volume Contract)**:
大纲中以 `ARC-NNN` 标识的硬剧情边界，包含固定章节闭区间、可验收卷目标、卷间因果、3-5 个截止里程碑和规划状态。
_Avoid_: 分卷建议、弹性卷计划

**章节执行契约 (Chapter Execution Contract)**:
冻结卷内每个 `CH-NNNN` 的必需剧情结果，包含章节任务、前置状态、核心冲突、结果变化、卷目标贡献、章末牵引和关联里程碑。
_Avoid_: 章节细纲、剧情分支 (无法表达硬结果约束)

**剧情对齐 (Plot Alignment)**:
正文与事务绑定的卷契约和章节执行契约完全一致，且没有未授权重大叙事事实的状态。
_Avoid_: 大致遵循、方向一致 (允许累积偏航)

**章末牵引 (Chapter-End Pull)**:
每章结尾用于推动读者进入下一章、且服务既定主线的危机、揭示、目标升级或情绪悬停；它不必成为可跨章追踪的正式悬念钩子。
_Avoid_: 悬念钩子、伏笔 (需要稳定 ID 的对象)

**卷规划修订 (Plan Revision)**:
通过 `修订卷规划 ARC-NNN` 对指定卷全部剩余章节做影响审计，并在用户批准后最小修改未发布章节契约、递增修订号和重新冻结的事务。
_Avoid_: 自动补章、边写边改、正文修订

**只读构思 (Read-only Preview)**:
`构思第 N 章`，只输出一个受冻结契约约束的执行方案和审计，不创建事务或修改文件。
_Avoid_: plan 模式、构思章节

**文本润色 (Text Polish)**:
只改变 staging 正文的语言、节奏、感官描写、物理化和去 AI 味，不负责补字数、验证、状态回写或归档。
_Avoid_: AI润、章节审计、内容扩充

**六维审计矩阵 (Six-Dimension Audit)**:
对章节进行体系纯度、战力平衡、时间线、物品消耗、地理跨度、人物OOC 六维一致性校验的规范 (`world-audit.md`)。
_Avoid_: 世界观检查、逻辑校验

**叙事线索注册表 (Narrative Thread Registry)**:
`world/hooks.md`, 统一保存活跃悬念钩子与伏笔，但两类对象使用独立 ID 和生命周期。
_Avoid_: 伏笔表、钩子表 (无法表达双对象边界)

**悬念钩子 (Narrative Hook)**:
制造近期阅读驱动力的未解决问题、危机或承诺，使用 `HOOK-NNNN`；解决它不要求预先埋设隐藏事实。
_Avoid_: 伏笔、线索 (语义不同)

**伏笔 (Foreshadowing Seed)**:
已写入正文、用于支撑未来揭示或反转的可追踪事实，使用 `SEED-NNNN`；正式回收必须证明与埋设事实的因果连接。
_Avoid_: 钩子、悬念 (语义不同)

**去 AI 味**:
依据 `style-guide.md` 黑名单词表与符号禁令, 清除正文 AI 工业感、保证文风统一的审计动作。
_Avoid_: 润色、文风优化 (不等价)

**风格身份锚点 (Style Basis)**:
`style-guide.md` frontmatter 中记录作品书名、流派、主调、主角/叙事身份设定、金手指和核心禁忌的短字段集合；机器只硬校验书名匹配和字段存在，其余字段用于重大设定变更时的 Agent 语义审查。
_Avoid_: World Bible 指纹、自动风格失效标记 (过严)

**叙事层泄漏 (Narrative-Layer Leakage)**:
正文暴露 Harness ID、章节结构、作者或读者身份、剧情安排、创作过程或外部镜头调度，使叙述跳出小说世界的违规呈现。
_Avoid_: 内部编号问题、打破第四面墙 (只覆盖部分表现)

**等义呈现修订 (Presentation-Equivalent Revision)**:
只改变已发布正文的符号、称谓或自然承接方式，不改变事件、因果、人物行为、信息差及 World Bible 语义状态的章节修订。
_Avoid_: 剧情修订、重写历史

**归档 (Archive)**:
按 `archiving-spec.md` 规则将已完成卷/离场人物/消耗道具迁移至 `world/archive/`, 主文件仅保留轻量索引链接的操作。
_Avoid_: 清理、删除 (语义不同)

**条件归档 (Conditional Archive)**:
完整创作指令授予的一次到期归档授权；只有触发条件满足且迁移预览无歧义时自动执行。
_Avoid_: 每章归档、静默清理

**确定性门禁 (Deterministic Gate)**:
由脚本机械判定并返回明确通过或失败结果的阻断规则，例如字数、格式、路由完整性与证据结构校验。
_Avoid_: 语义审计、Agent 自审

**语义门禁 (Semantic Gate)**:
由 Agent 对创作语义作出判断并提交结构化证据，程序验证证据完整性与结论是否允许继续，但不替代语义判断。
_Avoid_: 确定性检查、主观口头结论

**语义证据 (Semantic Evidence)**:
语义门禁提交的结构化判断依据，至少包含结论、来源文件及适用的章节或实体 ID；引用正文时附内容摘要值，执行器只校验结构、引用与摘要一致性。
_Avoid_: 模型认为合理、无来源总结

**门禁结果 (Gate Result)**:
门禁统一返回 `PASS`、`WARN`、`FAIL` 或附带原因的 `NOT_APPLICABLE`；必需结果缺失、证据缺失或状态未知均视为 `FAIL`，`PENDING` 只用于事务子状态。
_Avoid_: Emoji 判定、自由文本状态

**混合执行架构 (Hybrid Execution Architecture)**:
由 Manifest 声明命令路由与门禁编排，确定性脚本执行可机械验证的约束，Agent 负责创作与语义判断并提交结构化证据的 Harness 架构。
_Avoid_: 提示词规范库、全自动写作引擎

**事务执行器 (Transaction Executor)**:
正式章节、World Bible 与归档写入的唯一程序入口；负责推进事务状态、验证门禁与证据、应用变更集、保证幂等并记录恢复点，不负责生成创作内容。
_Avoid_: 内容生成器、普通校验脚本、Agent 直接写入

**章节事务 (Chapter Transaction)**:
以 `TX-CH-NNNN-RNN` 标识并持久化的一次完整章节写入，包含准备阶段、提交阶段和归档子状态。
_Avoid_: 自动写作流程 (缺少状态语义)

**事务记录 (Transaction Record)**:
保存于 `world/.transactions/TX-CH-NNNN-RNN.yaml` 的事务、门禁证据、变更集、摘要、幂等键与恢复点的唯一机器事实；人类可读输出仅由其渲染，不作为状态来源。
_Avoid_: Markdown 事务日志、执行报告

**准备阶段 (Prepare Phase)**:
在 staging 中完成正文、文本处理、最终门禁和 World Bible 变更集，尚未修改正式章节或 World Bible 的事务阶段。
_Avoid_: 草稿阶段、发布前检查

**提交阶段 (Commit Phase)**:
发布已验证正文、应用已准备的 World Bible 变更并执行后置一致性校验的事务阶段。
_Avoid_: 保存、更新世界

**周期原创性审计 (Periodic Originality Audit)**:
在初始化后、每 10 章、卷结束或核心设定变化时执行的长线原创性与结构风险门禁。
_Avoid_: 每章原创评分、单章去套路

**决策摘要 (Decision Summary)**:
Agent 对外提供的简短判断依据，包含引用文件、关键约束和风险，不包含完整内部推理链。
_Avoid_: Thought、思维链
