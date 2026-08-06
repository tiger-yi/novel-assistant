# Novel Assistant — 创作 Harness 域词汇表

本上下文描述 Novel Assistant 的 Agent 创作工作台 (harness) 领域: 命令协议、规范地图、World Bible 与创作闭环中使用的核心术语。

## Language

**World Bible**:
项目核心的结构化世界观数据文件集合 (`world/*.md`), 由 outline/characters/power/timeline/inventory/geography/hooks/chapter-summary 组成, 是当前规范化状态的事实来源；已发生事件以发布章节为证据，冲突按 `state-management.md` 处理。
_Avoid_: 设定文件、数据文件 (过泛)

**命令协议 (Command Protocol)**:
每个核心指令 (初始化世界/更新世界/...) 对应的独立执行规范文件, 存放于 `writespec/commands/*.md`, 定义触发词、功能与执行流程。
_Avoid_: 命令文档、指令说明

**context.manifest.yaml**:
novel-harness 的机器可读路由清单, 是规范加载顺序、世界数据加载顺序与验证命令的唯一事实来源。
_Avoid_: 配置文件、地图文件 (语境重叠时)

**加载顺序 (Loading Order)**:
执行任务前读取上下文与 World Bible 的既定先后次序, 由 manifest 的 `loading_policy` 与 `world_data.default_order` 定义。
_Avoid_: 读取流程、初始化步骤

**五步登仙 (Five-Step Genesis)**:
初始化世界时引导用户从五个维度 (流派/金手指/开局/世界观/情感) 通过多选构建世界观基石的交互协议, 现扁化并入 `init-world.md`。
_Avoid_: 创建向导、初始化引导

**ReAct 工作流**:
章节创作采用决策摘要-行动-观察循环，由 `chapter-creation-spec.md` 定义构思、初稿与最终门禁；对外只保留文件依据、关键约束和风险。
_Avoid_: 创作流程 (过泛)

**创作指令 (Create Chapter Command)**:
`创作第 N 章`，自动采用推荐分支并完成准备、提交、状态回写和条件归档的一次完整章节事务。
_Avoid_: 撰写章节、构思并写作、写第 N 章

**只读构思 (Read-only Preview)**:
`构思第 N 章`，只输出细纲、候选分支和审计，不创建事务或修改文件。
_Avoid_: plan 模式、构思章节

**文本润色 (Text Polish)**:
只改变 staging 正文的语言、节奏、感官描写、物理化和去 AI 味，不负责补字数、验证、状态回写或归档。
_Avoid_: AI润、章节审计、内容扩充

**六维审计矩阵 (Six-Dimension Audit)**:
对章节进行体系纯度、战力平衡、时间线、物品消耗、地理跨度、人物OOC 六维一致性校验的规范 (`world-audit.md`)。
_Avoid_: 世界观检查、逻辑校验

**去 AI 味**:
依据 `style-guide.md` 黑名单词表与符号禁令, 清除正文 AI 工业感、保证文风统一的审计动作。
_Avoid_: 润色、文风优化 (不等价)

**归档 (Archive)**:
按 `archiving-spec.md` 规则将已完成卷/离场人物/消耗道具迁移至 `world/archive/`, 主文件仅保留轻量索引链接的操作。
_Avoid_: 清理、删除 (语义不同)

**条件归档 (Conditional Archive)**:
完整创作指令授予的一次到期归档授权；只有触发条件满足且迁移预览无歧义时自动执行。
_Avoid_: 每章归档、静默清理

**Gate (门禁)**:
必须执行确定性验证后方可声称任务完成的门控规则 (字数/符号/审计/闭环)。
_Avoid_: 检查项、验收标准 (过泛)

**章节事务 (Chapter Transaction)**:
以 `TX-CH-NNNN-RNN` 标识并持久化的一次完整章节写入，包含准备阶段、提交阶段和归档子状态。
_Avoid_: 自动写作流程 (缺少状态语义)

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
