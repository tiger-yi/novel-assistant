# 长篇小说原创性审计规范 (Originality Audit)

> 来源: 由原 `novel-originality-auditor` 技能转化。

识别并消除长篇小说中的"同质化"与"逻辑硬伤", 通过**世界观增色**与**剧情降噪**, 确保作品在百万字规模下具备核心竞争力。

## 核心流程 (Workflow)

遵循 **ReAct (Reasoning and Acting)** 框架, 在每个阶段输出可审计的简短依据:
`[决策摘要]` (引用现状/风险证据) -> `[Action]` (调用工具/检索) -> `[Observation]` (得出结论)。不得要求输出完整内部推理链。

### 1. 数据对齐 (Context Sync)
- **行动**: 读取 `world/outline.md`, `world/characters.md`, `world/power.md`, `world/geography.md`。
- **目标**: 评估 World Bible 完整性, 识别初期设定与长线主线的耦合度, 发现"设定废弃"风险。

### 2. 深度审计 (Deep Audit)
根据以下维度进行交叉审计 (详细指南见 [audit-dimensions.md](audit-dimensions.md)):
- **世界观与逻辑**: 识别"换皮"倾向, 检查势力冲突的利益逻辑。
- **战力与成长**: 模拟后期对战, 预判数值膨胀与金手指过强风险。
- **人设生命力**: 挖掘行为必然性, 识别"降智反派"与"模板主角"。
- **桥段降噪**: 对比 [trope-blacklist.md](trope-blacklist.md), 识别陈旧桥段并提供反转方案。
- **特定系统审计**: 代价机制、诡异经济、组织逻辑等 (见 [original-check-guide.md](original-check-guide.md))。

### 3. 创新建议与同步
- **方案生成**: 提供"稳健微调"与"底层革新"两套差异化方案。
- **自动化同步**: 根据用户确认, 更新 `world/` 目录下的核心文档。

## 输出规范 (Output Format)
### 🚩 长篇小说原创性审计报告
- **核心风险等级**: [🔴 崩溃风险 / 🟡 逻辑预警 / 🟢 逻辑稳健]
- **雷同项/崩坏点**: 具体列出名称、设定或桥段。
- **生命力诊断**: 评估中后期读者的"疲劳感"风险。

### 💡 差异化优化方案
- **方案 A (稳健微调)**: 不改动核心体系的局部优化, 针对深度审计的具体建议。
- **方案 B (底层革新)**: 针对"独特性"的世界观/金手指重构, 针对深度审计的具体建议。

### 🛠️ 同步确认
询问用户: "是否根据方案 X 更新 World Bible 核心文件?"

## 相关规范
- 深度审计维度: [audit-dimensions.md](audit-dimensions.md)
- 陈旧桥段黑名单: [trope-blacklist.md](trope-blacklist.md)
- 原创度提升手册: [original-check-guide.md](original-check-guide.md)
