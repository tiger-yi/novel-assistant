---
schema: novel-harness/improvements/v1
---

# 受控改进台账

本台账只记录依据 `writespec/continuous-improvement.md` 产生的改进提案。提案不具备规则效力。

## 提案

| ID | 状态 | 触发事件与证据 | 问题与根因 | 建议 | 最终去向 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| IMP-0001 | 已晋升 | 用户提供 AIGC 检测分析、片段5动作链低风险证据、`check-ai-rules.md`、短故事创作资料，并经 grilling 确认边界；三章样本 `.idea/001-退婚宴上的三重杀机.txt`、`.idea/002-斩龙局的死亡倒计时.txt`、`.idea/003-医院里的第一次铁口直断.txt` 复现 L1 模板词、L2 场景动作链不足和 L3 开局结构风险；用户批准晋升为普通规范。 | 现有 AI 润色侧重清理空泛语言和物理化，但缺少长篇适配的人味定义、动作因果链、认知偏差滤镜、反模板台词、情绪节拍和 AI 痕迹分层；若机械吸收检测对抗技巧，会破坏《观天神相》的老辣、爽利和受限视角。 | 候选改进方向：`chapter-polish.md` 处理 L1 语言层与 L2 场景层，新增动作链、低价值指纹细节、认知偏差滤镜、语义留白、意象投影、题材内陌生化、非阻断情绪节拍和长篇章节钩子验证；`originality-audit.md` 处理 L3 结构层，如人名撞库、高预测桥段和核心设定同质化。明确 AIGC 检测器结果只作为风险信号，不作为唯一质量目标；禁止机械化三短一长、固定字数长句、强制语气词或脏话；排除短故事的极端标签化、高频反转、快速清算、三行硬排版和第一人称优先。 | 已晋升为普通规范：`writespec/chapter-polish.md` 与 `writespec/originality-audit.md`。 |
| IMP-0002 | 已晋升 | 既有 CH-0003 润色曾以五种人工策略整改四处非对话引号；本次 `.idea/CH-0025-田庄.txt` 第 23、49、67 行再次出现对白中套用旧话引号，用户经 grilling 确认统一范围、表达决策树、语义门禁与执行器证据约束，并批准晋升为普通规范。 | `INV-CHAPTER-001` 已禁止旧话转述使用引号，但只列出改写类别，未按叙事目的说明如何选择；现有 `narrative-integrity` 也只要求任意语义证据，无法证明创作、润色和迁移实际执行了转述扫描。 | 在 `chapter-creation-spec.md` 增加事件概括、间接转述、关键措辞无引号表达和当场模仿的选择顺序；四条正文 pipeline 的 `narrative-integrity` 必须提交 `reported_speech_audit`，执行器按可选 `required_evidence` 与 evidence `key` 阻断缺失证据的提交。 | 已晋升为普通规范：`writespec/chapter-creation-spec.md`；门禁同步至 Manifest、相关命令协议、状态规范与执行器。 |
| IMP-0003 | 已晋升 | 小说签约审核以“故事爽点不够”驳回；`.idea/签约.txt` 提供即时回报与黄金三章参考；仓库审计证明现有章节契约只有 `task/conflict/outcome/closing_pull`，读者评价虽事后评分但写前没有爽点承诺、状态升级与滚动密度契约。新增测试稳定复现：启用治理后缺少 `payoff_contract`、高密度数量不足和相邻主类型重复仍会被旧校验器放行。用户经 `grill-with-docs` 逐项确认定义、等级、类型、密度、门禁、非追溯边界、已发布修订模式及 INV 晋升。 | 现有流程把“有结果”误当“有回报”，缺少写前规划、正文证据和跨章升级约束；相同破局表现可连续复用，钩子也可能替代即时兑现。 | 新增独立爽点兑现契约：大纲规划，章节事务提交证据，读者门禁验收；`high`/`standard` 密度档执行真实状态变化、类型轮换、防拆分和滚动高潮校验；润色只强化已有兑现；已发布目标继续复用 `创作第 N 章` 的批准后新修订模式。 | 已晋升为 `INV-PAYOFF-001`，唯一权威为 `writespec/payoff-spec.md`；同步 Manifest、模板、校验器、测试及相关流程引用。 |
| IMP-0004 | 已晋升 | 用户指出既有运行实例把 World Bible 候选放在 `chapters/.staging/TX-CH-0030-R01/outline.md`，而测试示例使用 `world/.staging/<txid>/world/outline.md`；仓库证据证明执行器只校验 `.staging`+事务 ID，未校验 staging 归属与目标目录一致，`tests/test_transaction_executor.py` 中的嵌套写法 (`world/.staging/<txid>/world/outline.md`) 与章节正文惯例 (`chapters/.staging/<txid>/CH-….txt`) 不一致。 | staging 路径归属规则缺失：同一事务中章节正文与 World Bible 候选可混放目录，清理、恢复与审计时难以判断归属；门禁仅检查路径含 `.staging` 与事务 ID，放行跨目录偏差。 | 统一为平铺规则：staging 路径必须等于 `<目标父目录>/.staging/<事务ID>/<目标文件名>`；World Bible 候选一律放 `world/.staging/<txid>/`，章节正文放 `chapters/.staging/<txid>/`，不再嵌套一层目标目录。执行器在 `_preflight_changes` 强制校验，并新增回归测试证明误放目录被拒。 | 已晋升为普通规范：`writespec/state-management.md` 准备阶段 Stage 规则；同步 `scripts/transaction_executor.py` 校验与 `tests/test_transaction_executor.py` 相关用例。 |

状态仅允许：`候选`、`已验证`、`已晋升`、`已拒绝`。
