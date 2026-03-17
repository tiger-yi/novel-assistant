---
name: chapter-polisher
description: 用于小说章节的深度润色、字数扩充、去 AI 味及世界观逻辑审计。当需要：(1) 对初稿进行文学性提升；(2) 检查并扩充章节字数以达标；(3) 确保章节内容与 World Bible（大纲、境界、人物等）保持一致；(4) 彻底清除 AI 痕迹及违禁符号时使用。
---

# 章节润色器 (Chapter Polisher)

本技能通过 **ReAct 循环**（字数检查 -> ReAct 扩充 -> 世界观验证 -> 叙事重构 ->格式与逻辑终审）提升章节质量，消除 AI 工业感并强化玄幻质感。

## 核心工作流 (Core Workflow)

### STEP 1.字数检查 (Word Count Check)
检查当前章节(未指定章节则是最新章节)字数是否达标（默认 2000 字）。
```bash
python .trae/skills/chapter-polisher/scripts/check_count.py <file_path> [--target 2000]
```
- **如果不达标 (< 目标值)**: 进入 **STEP 2**。
- **如果达标 (>= 目标值)**: 跳过扩充，直接进入 **STEP 3**。

### STEP 2. ReAct 扩充 (Expansion)
仅当字数不足时执行。
- **Thought**: 分析情节空白、情感节奏缺失或感官细节不足之处。
- **Action**: 插入新内容（对话、支线、环境描写）。
    - **关键技巧**: 应用 [physical-descriptor.md](references/physical-descriptor.md) 中的“物理化重组规则”，将抽象情绪转化为具体的生理反应和环境互动（Show, Don't Tell）。
- **Observation**: 确认字数显著增加。
- **Loop**: 重复直到满足字数要求。

### STEP 3. 世界观验证 (World Consistenc)
**核心步骤**。无论字数是否达标，都必须执行此步骤。
- **Thought**: 对照世界观圣经（时间线、角色、战力体系）验证章节内容（原文 + 扩充部分）。
- **Action**: 
    1. **阅读参考**：阅读 [world_validation_examples.md](references/world_validation_examples.md) 以了解审计标准。
    2. 将事件/状态与 `world/outline.md`,`world/power.md`,`world/timeline.md`,`world/inventory.md`,`world/characters.toml` 文件进行比对。
- **Observation**: 识别冲突（例如：已死角色登场、错误的境界战力）。
    - **Fix**: 如果存在冲突，立即修正内容。

### STEP 4. **叙事重构 (Refactoring)**:
- **必须首先执行**：
    1. 加载叙事重构指南[narrative-refactor.md](references/narrative-refactor.md)
    2. 加载物理化重组规则[physical-descriptor.md](references/physical-descriptor.md)
- **Thought**: 基于叙事重构指南和物理化重组规则分析正文内容是否需要优化
- **Action**: 应用七大维度逐段重写，强制执行“去 AI 化”。
- **Observation**:
    - **自检**: 重构指南的检查维度是否遗漏?,物理化重组规则是否应用?。
    - **红队扫描**: 参考 [red-team-editor.md](references/red-team-editor.md)。若发现任何平稳对仗或抽象抒情，必须即时重写。

### STEP 5. 格式与逻辑终审 (Final Format & Logic Audit)
**必须执行**。在完成润色后，必须进行最后一次扫描。

1.  **标点与符号审计 (Punctuation & Symbol Audit)**:
    - [ ] 100% 删除了 `【 】`、`[ ]`、`（ ）`。
    - [ ] 100% 删除了强调式加粗 `** **`。
    - [ ] 非对话文本中，100% 禁止使用单引号 `‘ ’` 或双引号 `“ ”` 包裹任何词语/术语/碑刻/口令/道具名；仅人物对话允许使用引号。
    - [ ] 替代表达：碑刻/匾额→“碑面刻字：镇、禁、诫”；口令/敕字→“他在心底敕一字：止”；术语首引→直接使用无引号。
2.  **字数最终验证 (Word Count Check)**:
    -   再次运行字数检查脚本。
    -   **如果不通过**: 返回 **STEP 3** 继续扩充。
3.  **最终报告 (Final Report)**:
    -   输出优化后的最终字数。
    -   明确声明已通过格式终审。

### STEP 6. 更新和归档世界观 (Update & Archive World)
1. **更新世界观**:
    - 更新World Bible 文件 `world/power.md`,`world/timeline.md`,`world/inventory.md`,`world/characters.toml`
    - 更新 `world/outline.md`的**执行管理进度表**、**悬念与线索管理**，检查**详细章节规划表**是否存在后续待创作章节,如果不存在补充1-3个待创作章节(章节标题字数随机2-8字)，存在则不补充;
2. **归档世界观**:按照[archiving-spec.md](references/archiving-spec.md)规则进行归档

## 输出规范 (Output Specification)

执行完成后，必须显式输出：

### 1. 世界观验证报告 (World Consistency Report)
对照 `world/` 数据，汇报验证详情：
- **验证项**: 
    - **境界纯度**: 体系是否混用（如玄幻中出现魔法）。
    - **战力平衡**: 是否存在越级击杀不合理或代价不足。
    - **时间线**: 闭关、赶路时间与角色成长是否冲突。
    - **物品消耗**: 使用的法宝/丹药是否在 `inventory.md` 中有记录。
    - **地理情报**: 消息传播速度是否符合地图设定。
- **验证结果**: [✅通过 / ⚠️已同步更新 / ❌发现逻辑硬伤（需重写）]

### 2. 叙事去味报告 (Narrative De-AI Report)
基于 `narrative-refactor.md` 的七大维度进行检查：
- **执行维度**: 颗粒度清理、认知偏差、冰山留白、节奏呼吸（7-2-1律动）、人性幽暗、命运反差、具象锚点。
- **检查结果**: 识别到的 AI 痕迹（如：高频连接词、面板化符号、解释性叙述）。
- **修改方向**: 物理化重组（Show, Don't Tell）、打碎长难句、植入感官噪点、删除作者说教。

### 3. 红队审计报告 (Red Team Audit Report)
基于 `red-team-editor.md` 的对抗性检查：
- **审计内容**: 
    - **违禁词/旁白**: 识别“透着”、“隐隐约约”、“他意识到”等解释词。
    - **比喻模板**: 锁定“像...一样”等乏味明喻。
    - **情绪词**: 锁定“震惊”、“绝望”等抽象描述。
    - **符号清理**: 除人物对话外，彻底清除 Key-Value 面板、列表、`【 】`、`[ ]`、`（ ）`、单引号 `‘ ’`、双引号 `“ ”` 等系统符号；任何非对话场景出现引号即判违规。
- **审计结果**: 列出具体违规段落及发现的“工业指纹”。
- **修改方案**: 替换为生理反应（胃部抽搐、指尖发抖）、物件承载、或直接删除冗余符号。
