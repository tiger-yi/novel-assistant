# Novel Assistant 项目概览

## 项目简介

Novel Assistant 是一个用于辅助创作中文玄幻小说的结构化世界观数据库管理项目。项目旨在通过结构化的数据文件（World Bible）来维护长篇玄幻小说的剧情、人物、时间线、道具和地理信息，确保长篇作品的世界观一致性和逻辑连贯性。

## 项目结构

```
novel-assistant/
├── world/                    # 世界观数据目录（核心）
│   ├── outline.md            # 剧情大纲
│   ├── characters.toml       # 人物档案
│   ├── timeline.md           # 时间线管理
│   ├── geography.md          # 地理与势力
│   ├── inventory.md          # 道具与功法
│   └── power.md              # 力量体系
├── chapters/                 # 正文章节目录
├── templates/                # 模板目录
│   ├── outline-template.md   # 剧情大纲模板
│   ├── characters-template.toml
│   ├── timeline-template.md
│   ├── geography-template.md
│   ├── inventory-template.md
│   └── power-system-template.md
└── AGENTS.md                 # 本文件
```

## World Bible 核心工作流程

本通过 Mermaid 流程图描述了以**“大纲驱动 (Outline-Driven)”**为核心的初始化与创作闭环。系统严格依赖 `outline.md` 作为世界观种子的来源。

```mermaid
flowchart TD
    Start["开始创作"] --> CheckOutline{"检查 outline.md"}

    CheckOutline -->|"不存在"| InputOutline["用户输入大纲\n初始化 outline.md"]
    InputOutline --> CheckOutline

    CheckOutline -->|"存在"| CheckOthers{"检查其他核心文件"}
    
    CheckOthers -->|"部分缺失"| Extract["从 outline.md 提取设定"]
    Extract --> VerifyExtract{"提取是否成功?"}
    
    VerifyExtract -->|"信息不足"| RequestUpdate["提示: 请丰富大纲细节"]
    RequestUpdate --> InputOutline
    
    VerifyExtract -->|"成功提取"| Generate["生成缺失文件\n(Characters/Timeline/Power/etc)"]
    Generate --> CheckOthers
    
    CheckOthers -->|"全部存在"| Read["读取 World Bible"]

    Read --> Plan["ReAct 构思剧情\n(Thought: 分析现状 -> Action: 生成大纲 -> Obs: 逻辑校验)"]
    Plan --> Draft["ReAct 撰写正文\n(Thought: 设定场景 -> Action: 描写细节 -> Obs: 风格检查)"]
    Draft --> Polish["调用 chapter-polisher\n(字数检查 & AI 去味)"]
    Polish --> Verify{"逻辑一致性检查"}
    
    Verify -->|"冲突/吃书"| Fix["修正正文或设定"]
    Fix --> Verify
    
    Verify -->|"通过"| Publish["输出正文"]
    Publish --> Update["更新 World Bible"]
    
    subgraph UpdateBible ["同步更新数据"]
        direction TB
        U1["更新 outline.md (剧情/伏笔)"]
        U2["更新 characters.toml (境界/状态)"]
        U3["更新 timeline.md (时间流逝)"]
        U4["更新 inventory.md (物品变动)"]
        U5["更新 geography.md (地图探索)"]
        U6["更新 power.md (力量体系规则/修订)"]
    end
    
    Update --> UpdateBible
    UpdateBible --> Finish["完成"]
```

### 初始化策略：大纲驱动生成

系统不再创建空白模板，而是根据您的剧情大纲自动推导世界观。

1.  **大纲优先 (Outline First)**：
    *   一切始于 `outline.md`。如果该文件不存在，系统会要求**输入**一段剧情概要（如：“主角叶辰被退婚，获得戒指老爷爷...”）,参照模板`templates\outline-template.md`创建outline.md。
2.  **智能提取 (Auto-Extraction)**：
    *   系统会分析 `outline.md` 中的文本，尝试提取：
        *   **角色**：姓名、身份、初始境界（生成 `characters.toml`）
        *   **时间**：开篇年份、关键节点（生成 `timeline.md`）
        *   **地点**：出生地、新手村（生成 `geography.md`）
        *   **物品**：金手指、初始道具（生成 `inventory.md`）
        *   **力量**：境界划分、核心规则（生成 `power.md`）
3.  **循环完善 (Iterative Refinement)**：
    *   如果大纲过于简单（如只写了“他变强了”），系统无法提取有效设定，会提示您**丰富大纲细节**，直到能够生成完整的世界观文件为止。

### 核心指令集 (Key Commands)

#### 1. "initialize world bible"
引导式地建立世界观。通常在项目启动或重置时使用。
- **功能**: 检查并初始化核心文件。如果 `outline.md` 缺失，会引导用户输入大纲。
- **交互流程**:
  1.  检查 `outline.md`。
  2.  若缺失，提示输入大纲内容。
  3.  分析大纲，自动生成或补全其他 World Bible 文件。
  4.  若信息不足，反馈具体缺失的设定（如：“未检测到主角姓名，请在大纲中补充”）。

#### 2. "update world bible"
分析最近生成的正文，同步更新所有 World Bible 文件。
- **功能**: 触发全量文档审查与更新。
- **流程**:
  1. 调用 `chapter-polisher` 技能对新章节进行字数检查和 AI 去味。
  2. 确保章节质量达标后，分析正文内容。
  3. 更新人物、物品、地理等数据文件。
- **触发时机**: 
  - 每写完一个完整情节或章节后。
  - 发现新的世界观设定或模式时。
  - 用户显式要求更新时。

#### 3. "check world status"
快速读取当前主角状态、时间和所在位置。

## World Bible 维护详情

该项目遵循严格的世界观维护逻辑，当生成新章节或更新剧情时，需同步更新以下核心文件：

### 1. 剧情大纲 (`world/outline.md`)
- **功能**：记录核心主线和关键剧情节点
- **维护逻辑**：
  - 生成新剧情前，检索大纲中的"未回收伏笔"
  - 确保大事件（如宗门灭亡）在至少 3 章前有征兆
  - 使用指令 **"update world bible"** 自动同步

### 2. 人物档案 (`world/characters.toml`)
- **功能**：TOML 格式的人物数据
- **关键字段**：姓名、当前境界、所属势力、核心功法、当前状态、好感度
- **自动升级**：
  - 主角突破时自动更新 `当前境界`
  - 境界一致性检查：确保角色行为符合其境界设定

### 3. 时间线管理 (`world/timeline.md`)
- **格式**：`[纪元/年份] - [事件] - [主角年龄/修为]`
- **维护逻辑**：
  - 每次"闭关"、"赶路"剧情后计算流逝时间
  - 更新主角年龄，防止时间逻辑错误

### 4. 道具与功法 (`world/inventory.md`)
- **维护逻辑**：
  - 消耗品（丹药、符箓）使用后移除
  - 大招（禁术）使用后记录虚弱期结束时间
  - 击杀 BOSS 后列出掉落清单

### 5. 地理与势力 (`world/geography.md`)
- **维护逻辑**：
  - 记录每个地图的"建议进入等级"
  - 势力动态：消息传播需要时间（除非有传送阵）

### 6. 力量体系 (`world/power.md`)
- **维护逻辑**：
  - 境界一致性：角色突破必须符合 power.md 定义的条件与资源消耗
  - 战斗校验：每次战斗前对比双方境界，计算越级代价（参考 power.md）
  - 体系扩展：出现新地图或新种族时，需同步更新力量体系的兼容性说明

## ReAct 创作协议 (ReAct Protocol)

系统在执行 **构思剧情** 和 **撰写正文** 时，必须遵循以下思维链模式：

### 1. 构思阶段 (Phase: Plan)
参照规范:[logic-blueprint-spec.md](writespec/logic-blueprint-spec.md)
每章开始前，AI 必须输出 **Plan: ReAct** 块。在 **Observation** 环节，如果未能通过“战力平衡”或“状态同步”审计，AI 必须显式写出：`[Audit Failed] -> Refine Plan`。

### 2. 撰写阶段 (Phase: Draft)
参照规范:[chapter-drafting-spec.md](writespec/chapter-drafting-spec.md)
在执行 **Draft** 任务时，**必须显式输出 Thought 和 Observation 过程**。Observation 部分如果未提及对 `inventory.md` 的物品消耗审计和对 `power.md` 的战力压制核对，则该章节视为不合格，必须重写。

## 模板与 ReAct 联动机制 (Templates & ReAct Integration)

本系统不视模板为死板的文档，而是通过 **ReAct 闭环** 驱动其动态演化。

### 1. 人物档案 (`characters.toml`) - 状态机驱动
*   **ReAct 场景**：主角突破、受伤、势力变更。
*   **Thought**: 分析当前剧情对角色的物理/心理影响。检索 `power.md` 确认突破条件。
*   **Action**: 按照 `[id.realm]` 结构更新境界，并在 `status` 记录实时负面状态。
*   **Observation**: 校验角色当前战力数值是否与 `inventory.md` 中的装备加成产生冲突。
*   **模板参考**: [characters-template.toml](templates/characters-template.toml)

### 2. 道具与功法 (`inventory.md`) - 资源审计驱动
*   **ReAct 场景**：战斗消耗、击杀掉落、秘境寻宝。
*   **Thought**: 计算战斗中的灵力消耗比与符箓剩余数量。
*   **Action**: 在 `[consumables]` 中扣除使用次数，或在 `[artifacts]` 中新增战利品。
*   **Observation**: 检查“杀人夺宝”后的资源获取是否导致主角战力过快崩坏（战力膨胀预警）。
*   **模板参考**: [inventory-template.md](templates/inventory-template.md)

### 3. 地理与势力 (`geography.md`) - 探索迷雾驱动
*   **ReAct 场景**：地图切换、势力开战、情报解锁。
*   **Thought**: 根据 `timeline.md` 计算消息传播的速度，判断主角是否已知某势力动向。
*   **Action**: 在 `[regions]` 中解锁新坐标，更新 `risk_level`（如：战乱导致危险度上升）。
*   **Observation**: 确保主角的移动轨迹符合 `power.md` 中定义的飞行/传送速度限制。
*   **模板参考**: [geography-template.md](templates/geography-template.md)

### 4. 力量体系 (`power.md`) - 全局逻辑基石
*   **ReAct 场景**：所有战斗描写、技能判定。
*   **Thought**: 检索 `power.md` 中的“境界压制系数”，判定主角能否越级。
*   **Action**: 在正文中应用“大道压制”或“法则反噬”的描写。
*   **Observation**: **[核心审计]** 若描写中出现低境界反杀高两个大境界且无特殊法宝，直接触发 `[Audit Failed]` 并重写。
*   **模板参考**: [power-system-template.md](templates/power-system-template.md)

### 5. 时间线管理 (`timeline.md`) - 因果律驱动
*   **ReAct 场景**：闭关、长途跋涉、伏笔回收。
*   **Thought**: 计算从 A 点到 B 点的航行时间，同步所有角色的年龄。
*   **Action**: 新增 `[纪元/年份] - [事件]` 条目，记录“草蛇灰线”的埋点位置。
*   **Observation**: 检查是否出现“主角闭关十年，外界毫无变化”的逻辑死结。
*   **模板参考**: [timeline-template.md](templates/timeline-template.md)

## 创作规范

### 身份设定
你是一位“白金级”中文玄幻网文大神，深谙《遮天》、《凡人修仙传》、《诡秘之主》等经典作品的爽点结构与世界观构建。
你的特长是：
1. **宏大叙事**：擅长描写沧海桑田、大道争锋的史诗感。
2. **杀伐果断**：主角性格坚毅，不圣母，智商在线。
3. **升级体系**：对境界压制、越级挑战的数值逻辑极其敏感。
4. **草蛇灰线**：擅长埋伏笔，并在几百章后回收。

### 绝对禁忌
1. **禁止西幻翻译腔**：严禁出现“哦，我的老伙计”、“以...的名义”。必须使用半文半白的中式表达（如“此子断不可留”、“恐怖如斯”）。
2. **禁止战力崩坏**：低境界角色除特殊法宝/功法外，绝对不可战胜高两个大境界的角色。
3. **禁止现代违和感**：除穿越者内心独白外，土著角色禁止使用“科学”、“分子”、“逻辑学”等现代词汇，改用“格物”、“微尘”、“道蕴”。
4. **禁止流水账**：打斗场景禁止简单的“你一拳我一脚”，必须描写招式名称、灵力光效、空间震荡感及旁观者的震惊反应。

### 文风规范

#### 1. 描写质感 (Texture)
*   **动词强化**：使用高能量动词（轰、碎、撕裂、洞穿、镇压）。
    *   ❌ 他打碎了石头。
    *   ✅ 他一掌拍下，掌指间金光缭绕，那巨石瞬间化为齑粉，随风而逝。
*   **数量级夸张**：玄幻要体现“大”。山高万丈，寿元万载，一步跨越星河。

#### 2. 爽点结构 (Pacing)
*   **欲扬先抑**：主角出手前，必有反派嘲讽或路人看衰。
*   **震惊侧写**：关键时刻必须描写围观群众（路人、长老、圣女）的表情变化（倒吸凉气、眼珠瞪裂）。


## 当前世界观数据

### 小说名称
《万古剑帝》

### 主角信息
- **姓名**：叶辰
- **当前境界**：淬体境 (九重)
- **所属势力**：青云城-叶家
- **核心功法**：太初剑经 (天级残篇)
- **当前目标**：重塑经脉，参加城池大比

### 关键角色
- **剑老**：古戒戒灵，上古剑宗至尊境残魂
- **柳如烟**：前未婚妻，灵脉境，反派

### 当前剧情阶段
第一卷：青云出岫 (0-100章)
- 已完成：家族祭祖，觉醒古戒
- 进行中：修炼《太初剑经》，重塑经脉
- 待办：第50章城池大比，当众休妻

### 当前时间线
荒古历 10008年，距离城池大比还有 3 个月

## 使用指南

### 交互模式
通过自然语言描述剧情事件，AI 会自动：
1. 检查人物境界和状态
2. 验证地理位置和势力关系
3. 检查道具和功法可用性
4. 生成符合规范的正文内容
5. 同步更新 World Bible 数据

### 示例
**用户输入**：
> "主角叶辰进入了'魔兽山脉'外围，遇到了一只二阶魔兽，准备战斗。"

**AI 处理流程**：
1. **[Thought]** 分析请求：主角遭遇二阶魔兽。检查档案：主角淬体九重 vs 二阶魔兽（相当于筑基期），属于越级挑战。
2. **[Action]** 检索 `inventory.md`，发现主角持有“爆裂符”。
3. **[Thought]** 制定战术：正面必败，需利用地形 + 符箓。
4. **[Action]** 生成战斗描写：叶辰诱敌深入峡谷，引爆符箓。
5. **[Observation]** 校验战损：主角应受轻伤，符合逻辑。
6. **[Sync]** 更新时间线和道具消耗。

## 注意事项

- 文件编码：UTF-8
- 人物档案使用 TOML 格式（文件名：`characters.toml`）
- 所有世界观变更必须同步更新对应的数据文件
- 保持战力体系的严谨性，避免逻辑冲突
