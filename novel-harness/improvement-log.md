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

状态仅允许：`候选`、`已验证`、`已晋升`、`已拒绝`。
