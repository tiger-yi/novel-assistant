# 读者评价门禁

`reader-evaluation` 是 `创作第 N 章` 的 staging 正文质量门禁。`.idea/snake.md` 可作为毒蛇文本读者的草案输入，但本文件才是正式规范来源。

本门禁只评价并驱动局部受限重润色，不获得改剧情、改世界状态或发布正文的权限。

## 适用范围

- 只用于 `创作第 N 章` 的完整章节事务。
- 不用于 `构思第 N 章`。
- 不用于 `润色章节 CH-NNNN` 或 `润色当前章节`。
- 评价对象必须是事务 staging 中经过一次 `chapter-polish.md` 纯文本润色后的正文候选。
- 评价前必须已完成 `signing-first-impression-risk` 门禁；本门禁评价多读者质量，不替代签约首感风险。

## 流程位置

章节创作流程中，本门禁位于 `polish` 之后、`chapter-format` 之前：

```text
draft -> polish -> signing-first-impression-risk -> reader-evaluation -> chapter-format -> narrative/world/plot/thread gates -> commit
```

若读者评价触发自动重润色，重润色后的正文必须重新进入后续字数、格式、叙事、世界观、剧情和线索门禁。旧门禁结果不得覆盖新正文。

## 读者画像

读者评价由三个固定画像组成。每个画像使用独立维度评分，先归一到 10 分，再按权重聚合。

| 画像 | 聚合权重 | 关注点 |
| :--- | :--- | :--- |
| 目标类型读者 | 40% | 翻页欲、爽点兑现、主角能动性、情绪回报、结尾钩子 |
| 世界观沉浸读者 | 30% | 设定后果、战力可信、资源/伤势/信息差、环境专用性、伏笔承接 |
| 毒蛇文本读者 | 30% | 叙事引擎、人物血肉、语言咬合力、结构骨架、情感重量、独特声音 |

每个画像内部先按维度权重得到画像分。若单个维度触发结构性或世界状态阻断，不得用其他高分抵消。

## 毒蛇校准

读者评价默认从 7.0 起评，而不是从 8.5 起评。评分者必须先找扣分点，再确认亮点是否足以抬分。

- `7.0-7.9` 表示可发布但有明确伤口，是常见好章区间。
- `8.0-8.4` 表示强章，必须同时具备清晰亮点和可说明的小缺口。
- `8.5-8.9` 表示同类题材显著优秀，必须给出同维度反证审查。
- `9.0+` 表示近乎无可替代的标杆表现；单章内不得轻易给出，且同一报告最多允许 2 个维度达到 `9.0+`，除非提供强证据说明。

以下情况必须压分或判为评价证据不足：

- 所有维度都 `>= 8.5`，但没有逐维负面证据。
- 写出“无扣分项”“无建议”后直接 `PASS`。
- 只引用亮点，不引用任何问题段落或弱点定位。
- 高分理由只复述剧情事实，没有说明为什么高于普通合格章。
- 世界观、战力或伏笔分数高于 8.5，却没有引用对应 World Bible 或前文承接证据。

高分上限规则：

- 没有负面短引或明确弱点定位时，聚合分不得高于 `7.9`。
- 没有 `auto_actionable_suggestions` 时，聚合分不得高于 `8.0`；若确实无需重润色，必须说明至少 3 个“保留但不修”的轻微问题。
- 任一画像缺少逐维证据时，该画像分不得高于 `7.5`。
- 任一维度只有亮点、没有扣分依据时，该维度分不得高于 `8.0`。
- 若报告声称没有任何扣分项，本门禁状态必须为 `MANUAL_DECISION_REQUIRED`，要求重评。

评价报告必须包含“毒蛇反证审查”小节，至少回答：

1. 本章最该被扣分的三处在哪里。
2. 哪些问题不能自动改，因为会触碰结构或世界状态。
3. 哪些亮点必须保护，但不能因此掩盖弱点。
4. 为什么最终分数不是更低，也为什么不是更高。

### 目标类型读者

目标类型读者判断章节是否让目标网文读者愿意继续读下去。

| 维度 | 内部权重 | 9-10 | 7-8 | 5-6 | 3-4 | 1-2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 翻页欲 | 25% | 开篇迅速进入有缺口的当下，场景间持续制造下一步欲望 | 推进稳定，少量说明或停顿削弱紧迫感 | 故事在移动，但冲突动机或问题钩子偏钝 | 大量铺陈和等待，读者容易跳段 | 几乎没有继续读的理由 |
| 爽点兑现 | 25% | 压力、反击、获得、揭露或选择有清晰回报，且代价可信 | 有回报但力度或延迟略弱 | 承诺存在，兑现含糊或只靠旁白说明 | 爽点被解释、稀释或错位 | 承诺落空，读者被吊起后无所得 |
| 主角能动性 | 20% | 主角以判断、行动和代价改变局面 | 主角有主动动作，但部分关键推进来自外力 | 主角主要响应事件，选择空间偏小 | 主角像剧情工具，缺少有效选择 | 主角被动旁观或被强行推动 |
| 情绪回报 | 15% | 紧张、痛感、愤怒、快意或不甘从动作和细节中自然产生 | 有情绪段落，少量依赖直白抒写 | 情绪可理解但停在标签层 | 情绪与事件脱节或反复说明 | 读者无法进入情绪 |
| 结尾钩子 | 15% | 章末问题具体、迫近，并直接服务卷目标 | 有钩子但锋利度或承接略弱 | 结尾只是事件暂停，牵引一般 | 结尾松散，下一章动机不明 | 无章末牵引 |

目标类型读者不得要求新增背叛、死亡、新法宝或改变章节结果来制造爽点；这类建议必须归入 `STRUCTURAL_SUGGESTION_BLOCKED`。

### 世界观沉浸读者

世界观沉浸读者判断章节是否像从当前世界自然长出。

| 维度 | 内部权重 | 9-10 | 7-8 | 5-6 | 3-4 | 1-2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 设定后果 | 20% | 已有规则稳定影响人物选择、代价和局势 | 设定有后果，少量地方仍靠解释 | 设定存在但与事件绑定较弱 | 设定像背景贴纸，后果稀薄 | 设定可删除而故事不变 |
| 战力可信 | 25% | 攻防、境界、限制和胜负条件均符合 `world/power.md` | 基本可信，个别强弱呈现需证据补足 | 胜负能理解但限制和代价模糊 | 战力表现明显漂移 | 违反力量体系或核心胜负逻辑 |
| 资源/伤势/信息差 | 25% | 道具消耗、伤势延续、时间压力和知情边界闭合 | 大体闭合，少量状态需要更清晰落点 | 状态存在但读者难以追踪 | 消耗、伤势或知情边界多处松动 | 关键状态自相矛盾 |
| 环境专用性 | 15% | 场景细节具有本世界专属性，替换背景会损失意义 | 有专用细节，少量通用描写 | 环境可感但类型化 | 场景像通用舞台 | 环境与世界观脱节 |
| 伏笔承接 | 15% | `HOOK-*`、`SEED-*` 被自然承接，状态不越权 | 有承接但证据密度略弱 | 伏笔存在感弱或承接生硬 | 伏笔被遗忘或误导读者 | 伏笔状态或证据被越权改变 |

世界观沉浸读者发现事实、战力、资源、伤势、时间线、信息差或线索生命周期问题时，必须优先标记 `WORLD_STATE_BLOCKED`，不得用文笔或爽点高分抵消。

### 毒蛇文本读者

毒蛇文本读者继承毒蛇评分的文本锋利度，但需服务长篇连载稳定性。

| 维度 | 内部权重 | 9-10 | 7-8 | 5-6 | 3-4 | 1-2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 叙事引擎 | 20% | 冲突、信息释放和段落钩子形成持续牵引 | 推进稳定，少量段落降速 | 冲突在动但张力不足 | 说明和无效描写明显拖慢 | 场景缺少因果牵引 |
| 人物血肉 | 20% | 角色欲望、恐惧、矛盾、身体感和声音可辨 | 主角清楚，配角或对话略功能化 | 角色能执行剧情但内在冲突不足 | 角色扁平、对话机械 | 角色像符号或纸板 |
| 语言咬合力 | 15% | 动词精准，名词具体，句子有速度和重量 | 清晰有力，少量陈词或冗余 | 通顺但平，抽象词偏多 | 拖沓、重复、虚浮修辞多 | 用词苍白或语法影响阅读 |
| 结构骨架 | 15% | 场景功能清楚，转折和呼应稳固 | 结构顺畅，局部长短略失衡 | 场景衔接松散或有填充段 | 顺序和重心混乱 | 事件随机堆叠 |
| 情感重量 | 15% | 情绪由动作、物件、身体反应和潜台词渗出 | 有触动点，少量直白抒写 | 情绪可见但表面化 | 情绪标签化，读者无感 | 情绪虚假或冷漠 |
| 独特声音 | 15% | 视角、语气和节奏有本书指纹 | 有风格但偶尔滑入通用表达 | 风格模糊，可替代性强 | 模仿感或工业感明显 | 缺少可辨认气质 |

毒蛇文本读者可以指出删冗、节奏、人物和语言问题，但不得要求改变已冻结情节结果。需要改变结果才能解决的问题，必须转入 `manual_decision_suggestions`。

## 通用扣分项

通用扣分项直接作用于聚合分，并必须说明触发证据。若同一问题已在画像维度中扣分，通用扣分只记录一次，避免重复惩罚。

扣分必须先标记严重度，再套用幅度：

| 严重度 | 幅度 | 判定 |
| :--- | :--- | :--- |
| `minor` | -0.2 | 局部影响阅读，但不改变本章整体判断 |
| `moderate` | -0.4 | 明显压低一个画像维度，需要局部重润色 |
| `major` | -0.7 | 影响本章核心体验或多个维度，需要优先修 |
| `critical` | -1.0 或阻断 | 破坏核心因果、承诺兑现、世界状态或读者理解 |

以下问题触发硬阻断或自动化阻断分级，不得只用扣分抵消：

| 阻断项 | 触发条件 | 处理 |
| :--- | :--- | :--- |
| 核心因果断裂 | 读者需要依赖作者解释才能理解胜负、选择、获得、逃脱或揭露 | `STRUCTURAL_SUGGESTION_BLOCKED` |
| 主角关键失智 | 主角关键选择违背既有人设、目标或已知信息，且不是文本有意呈现的代价 | `STRUCTURAL_SUGGESTION_BLOCKED` |
| 章节承诺落空 | `chapter_promise` 的核心回报未兑现，章末也没有补偿性牵引 | 先判 `AUTO_ROUTE_COMMIT`，若必须改章节结果则 `AUTO_ROUTE_REVIEW` |
| 关键结果靠巧合 | 胜负、获得、逃脱、揭露或重要转折主要依赖未经铺垫的巧合 | `STRUCTURAL_SUGGESTION_BLOCKED` |
| 爽点必须改剧情才成立 | 需要新增事件、新因果、新死亡、新法宝或改章节结果才能修复 | `STRUCTURAL_SUGGESTION_BLOCKED` |
| 世界状态冲突 | 战力、资源、伤势、时间线、地理、信息差或伏笔状态与证据冲突 | `WORLD_STATE_BLOCKED` |

常规扣分项必须覆盖读者体验、结构、人物、语言和世界沉浸：

| 扣分项 | 默认严重度 | 触发条件 | 自动处理 |
| :--- | :--- | :--- | :--- |
| 开篇迟滞 | `moderate` | 前 300-500 字无明确问题、压力、目标或可感缺口 | `PACING_FIX` |
| 翻页钩子钝 | `moderate` | 场景间缺少下一步问题，读者没有追读压力 | `PACING_FIX` |
| 爽点错位 | `major` | 铺垫的是 A，兑现的是 B，读者预期收益落空 | 轻微可 `PACING_FIX`，涉及结果则阻断 |
| 压力不足 | `moderate` | 对手、环境、代价或时间压力不足以逼迫主角行动 | `PACING_FIX` 或 `WORLD_TEXTURE_FIX` |
| 对手降智 | `major` | 反派、阻力或环境为了让主角赢而明显变蠢 | 通常转人工，轻微可局部补压迫证据 |
| 主角能动性不足 | `major` | 关键推进主要来自外力、巧合或配角安排 | 涉及选择则阻断 |
| 场景空转 | `moderate` | 场景不推进冲突、信息、情绪、人物关系或伏笔 | `PACING_FIX` |
| 信息密度失衡 | `moderate` | 连续解释、设定堆叠或低收益信息压低阅读动力 | `TEXTUAL_FIX` 或 `PACING_FIX` |
| 信息释放失败 | `major` | 关键悬念过早说明、该解释处含糊，或读者无法判断因果 | 轻微可重润色，结构性转人工 |
| 章末钩子泛化 | `moderate` | 结尾只是“出事了”或事件暂停，没有具体下一章问题 | `PACING_FIX` |
| 情绪越权 | `moderate` | 旁白替读者宣布感动、愤怒、震撼，而非由动作细节产生 | `EMOTIONAL_FIX` |
| 情绪回报不足 | `moderate` | 压力、反击、失去或获得之后缺少读者可感回响 | `EMOTIONAL_FIX` |
| 人物声音同质 | `moderate` | 主角、配角、反派台词和反应可互换 | `TEXTUAL_FIX` |
| 人物动机悬浮 | `major` | 角色行动缺少欲望、恐惧、利益或代价支撑 | 轻微可补细节，结构性转人工 |
| 视角混乱 | `moderate` | 单章内无理由切换受限视角，导致读者混淆 | 可局部重润色，若需改事件则阻断 |
| 过度解释 | `minor` | 连续说明替代动作展示，明显压低张力 | `TEXTUAL_FIX` 或 `PACING_FIX` |
| 台词失声 | `minor` | 多个角色说话口吻不可区分 | `TEXTUAL_FIX` |
| 节奏停滞 | `moderate` | 大段描写或说明超过约 500 字且无动作、信息或情绪推进 | `PACING_FIX` |
| 语言虚浮 | `minor` | 抽象形容、套话、空泛比喻或低价值修饰密集出现 | `TEXTUAL_FIX` |
| 设定悬浮 | `moderate` | 设定只被解释，没有在选择、代价或环境中产生后果 | `WORLD_TEXTURE_FIX`，不得新增设定 |
| 环境通用 | `minor` | 换成任意客栈、山洞、街道、战场也不影响阅读 | `WORLD_TEXTURE_FIX` |
| 战力漂移 | `major` | 攻防、限制、代价或胜负条件缺少 `world/power.md` 支撑 | `WORLD_STATE_BLOCKED` |
| 资源/伤势松动 | `major` | 道具消耗、伤势延续、时间压力或信息差难以追踪 | `WORLD_STATE_BLOCKED` |
| 类型期待偏移 | `major` | 目标读者期待的爽、压迫、奇观、升级、解谜或反击长期没有被服务 | 轻微可重润色，结构性转人工 |

## 评分输出格式

评价报告必须用固定结构输出，避免自由评论漂移：

```yaml
reader_evaluation:
  round: R1
  chapter_id: CH-NNNN
  chapter_hash: "<hash>"
  personas:
    target_genre_reader:
      weighted_score: 0.0
      dimensions: []
    world_immersion_reader:
      weighted_score: 0.0
      dimensions: []
    viper_text_reader:
      weighted_score: 0.0
      dimensions: []
  aggregate_score: 0.0
  deductions:
    - name: ""
      severity: minor|moderate|major|critical
      penalty: 0.0
      evidence_refs: []
      suggestion_type: TEXTUAL_FIX|PACING_FIX|EMOTIONAL_FIX|WORLD_TEXTURE_FIX|STRUCTURAL_SUGGESTION_BLOCKED|WORLD_STATE_BLOCKED
  chapter_promise:
    core_reader_payoff: ""
    emotional_target: ""
    information_release: ""
    ending_pull: ""
  scene_diagnostics: []
  likely_drop_points: []
  auto_actionable_suggestions: []
  manual_decision_suggestions:
    auto_escalatable_manual: []
    auto_safe_structural_fix: []
    hard_manual_required: []
  risk_resolution_plan:
    mode: null
    priority_order: []
    immediate_action: ""
    safe_auto_fixes: []
    deferred_auto_fixes: []
    required_routes: []
    user_decisions: []
  status: PASS|PASS_WITH_AUTO_FIX|PASS_WITH_TARGET_MISS|BLOCKED|BLOCKED_WITH_REPAIR_PLAN|MANUAL_DECISION_REQUIRED
```

每个 `dimensions` 条目必须包含 `name`、`score`、`weight`、`evidence_refs`、`reason` 和 `suggestion_type`。缺少维度分、证据或建议分类时，本门禁不得放行。

每个 `deductions` 条目必须包含 `name`、`severity`、`penalty`、`evidence_refs`、`reason` 和 `suggestion_type`。`severity` 与 `penalty` 必须符合“通用扣分项”的严重度表；若人工调整幅度，必须说明原因。

每个 `dimensions` 条目还必须包含：

- `negative_evidence_refs`: 扣分或压分定位；没有则该维度最高 8.0。
- `score_ceiling_reason`: 若分数 `>= 8.0`，说明为什么没有被压到 7.x。
- `improvement_hint`: 至少一个可执行或不可执行的改进方向。

## 章节承诺与场景诊断

评分前必须先提炼本章的读者承诺，避免评价漂移为泛泛审稿：

若事务已启用 `INV-PAYOFF-001`，下列字段必须引用 `payoff-evidence.yaml` 中相同的爽点 ID、承诺和状态变化；评价器不得自行把钩子、危机或旁观者反应改判为新爽点。

- `core_reader_payoff`: 本章承诺兑现的核心爽点、压力反击、揭露、选择或获得。
- `emotional_target`: 本章希望读者最终留下的主要情绪。
- `information_release`: 本章释放、遮蔽或反转的关键信息。
- `ending_pull`: 章末牵引下一章的具体问题。

若正文无法支撑上述任一项，必须在对应画像和 `likely_drop_points` 中扣分或标记证据不足。

`scene_diagnostics` 用于把评分转化为可执行改稿意见。每个场景诊断至少包含：

- `scene_ref`: 场景或段落定位，不复制完整正文。
- `scene_function`: 该场景在本章中的功能，例如推进冲突、兑现爽点、沉淀情绪、释放信息或承接伏笔。
- `reader_expectation`: 读者进入该场景时自然期待什么。
- `quality_issue`: 若有问题，说明掉速、失真、失声、悬浮或回报不足的位置。
- `fix_path`: 可执行修法或不可自动修的原因。
- `protected_element`: 重润色时必须保护的锋利句、人物选择、信息差或情绪落点。

评价报告必须列出 `likely_drop_points`，预判目标读者最可能跳读、出戏、觉得水、觉得假或觉得不爽的位置。每个流失点必须包含定位、触发原因、影响画像和建议类型。

## 分数与阻断

- 总分为 10 分制，保留一位小数。
- 聚合分 = 目标类型读者分数 x 0.40 + 世界观沉浸读者分数 x 0.30 + 毒蛇文本读者分数 x 0.30。
- 聚合分 `< 7.0`: 阻断，最多 2 轮局部受限重润色和复评。
- 聚合分 `7.0-7.9`: 自动局部受限重润色 1 次；复评后只要仍 `>= 7.0`，不阻断最终发布。
- 聚合分 `>= 8.0` 且没有自动建议、流失点或未修目标缺口：`PASS`，直接进入后续门禁。
- 聚合分 `>= 8.0` 且存在低/中风险自动建议：`PASS_WITH_AUTO_FIX`，默认授权局部受限重润色 1 次并复评。
- 聚合分 `>= 8.0` 且仅存在保留性目标缺口、不可自动修但不影响发布的问题：`PASS_WITH_TARGET_MISS`，记录原因后进入后续门禁。
- 任一读者画像 `< 6.0`: 硬阻断，即使聚合分达标也不得放行。
- 多种高权限风险同时存在，且不能在读者评价门禁内安全自动修复时：`BLOCKED_WITH_REPAIR_PLAN`。

两轮低分修正后仍 `< 7.0`，或任一画像仍 `< 6.0`，事务保持未完成，保留 staging、评价报告、失败项和恢复点，等待人工决策。

报告存在 `likely_drop_points`、`negative_evidence_refs` 或 `auto_actionable_suggestions` 时，不得写“无通用扣分项”后直接 `PASS`。存在可自动修的低/中风险问题时必须使用 `PASS_WITH_AUTO_FIX`；存在越权问题时才使用 `MANUAL_DECISION_REQUIRED`。

`BLOCKED_WITH_REPAIR_PLAN` 表示已一键完成风险归并、修复排序和安全部分执行建议，但事务不得继续进入后续门禁。它不能直接提交章节、World Bible、伏笔或大纲变更。

## 自动重润色边界

自动重润色只允许针对扣分维度和对应段落进行局部受限调整，且必须符合 `chapter-polish.md`。

允许自动执行的建议类型：

- `TEXTUAL_FIX`: 删冗、动词精确、句式节奏、低价值描写压缩。
- `PACING_FIX`: 在既有事件内压缩说明、强化动作因果和信息释放。
- `EMOTIONAL_FIX`: 用动作、身体感、物件和潜台词强化既有情绪。
- `WORLD_TEXTURE_FIX`: 把已有设定写得更落地，但不得新增规则或状态。

禁止自动执行的建议类型：

- `STRUCTURAL_SUGGESTION_BLOCKED`: 涉及新事件、新因果、新背叛、新死亡、新法宝、改人物选择、改章节结果或改卷目标。
- `WORLD_STATE_BLOCKED`: 涉及 World Bible 事实、战力、道具、伤势、时间线、地理、信息差或伏笔状态变化。

禁止项不得在当前读者评价阶段直接改正文，但必须继续按四档自动化阻断分级处理。单章未发布候选且不改变冻结契约时优先 `AUTO_ROUTE_COMMIT`；影响后续章节契约、World Bible 核心事实或已发布事实时转 `AUTO_ROUTE_REVIEW`；需要用户接受长期风险或撤销叙事承诺时转 `HUMAN_REQUIRED`。

默认自动修复授权：

- `PASS_WITH_AUTO_FIX` 默认授权 `draft-worker` 按 `auto_actionable_suggestions` 局部受限重润色 1 次。
- 自动修复只允许 `risk_level` 为 `low` 或 `medium`，且 `suggestion_type` 属于允许自动执行的建议类型。
- 自动修复不得新增事件、新因果、新角色、新死亡、新法宝，不得改变章节 `task/outcome/conflict/closing_pull`、人物关键选择、World Bible 事实、伏笔状态或后续章节契约。
- `risk_level: high`、`STRUCTURAL_SUGGESTION_BLOCKED`、`WORLD_STATE_BLOCKED` 和 `hard_manual_required` 一律不得作为当前阶段文本修复直接执行；其中可由正确命令流程自动生成并验证候选的，进入 `AUTO_ROUTE_COMMIT` 或 `AUTO_ROUTE_REVIEW`。

当多种风险同时存在时，可一键生成 `risk_resolution_plan`，并只执行不依赖高权限结论的安全文本修复。若低/中风险文本修复所在段落受 `WORLD_STATE_BLOCKED`、`STRUCTURAL_SUGGESTION_BLOCKED` 或 `hard_manual_required` 影响，必须放入 `deferred_auto_fixes`，等待上游风险处理后再执行。

## 改稿建议结构

`auto_actionable_suggestions` 中每条建议必须能被 `draft-worker` 局部执行，且至少包含：

- `id`: 稳定建议编号。
- `priority`: `P0`、`P1` 或 `P2`；`P0` 表示影响放行或明显流失，必须优先处理。
- `suggestion_type`: 必须属于允许自动执行的建议类型。
- `target_dimension`: 对应画像和维度。
- `rewrite_span`: 建议影响的段落或场景范围。
- `expected_gain`: 预期改善的质量收益，使用 `low`、`medium` 或 `high`。
- `risk_level`: 自动改写风险，使用 `low`、`medium` 或 `high`。
- `instruction`: 面向重润色的具体动作，不得写成抽象评价。
- `must_preserve`: 不得误伤的剧情事实、人物选择、设定状态、伏笔和高光表达。

`manual_decision_suggestions` 必须拆分为三类，并附自动化阻断分级，减少不必要人工介入：

- `auto_escalatable_manual`: 可自动生成候选修法，但候选不得直接提交；用于需要比较方案但不改变事实的问题。
- `auto_safe_structural_fix`: 允许自动修复的低风险结构问题；前提是不改变章节结果、人物选择、World Bible、伏笔状态或后续契约。
- `hard_manual_required`: 必须人工确认的问题；只用于新增事件、新因果、新死亡、新法宝、改章节结果、改人物选择、改 World Bible、改伏笔状态、改后续章节契约等越权项。

`auto_safe_structural_fix` 的建议必须同时写明 `allowed_scope` 和 `forbidden_scope`。例如可增强现有战斗压迫感、混乱、险象和动作因果，但不得新增强敌、改变胜负结果或挪用下一章升级契约。

`auto_escalatable_manual` 和 `auto_safe_structural_fix` 不应默认等待人工。若只影响未发布当前章、可保持同一章节执行契约并通过后续门禁，应标记为 `AUTO_ROUTE_COMMIT`；若会调整未发布后续章节契约或 World Bible 核心事实，应标记为 `AUTO_ROUTE_REVIEW`。只有放弃/取消伏笔、改已发布事实、改卷目标、接受长期风险等不可逆事项才标记为 `HUMAN_REQUIRED`。

## 综合修复计划

当报告同时存在 `WORLD_STATE_BLOCKED`、`STRUCTURAL_SUGGESTION_BLOCKED`、`hard_manual_required`、`risk_level: high` 或多个低/中风险建议时，必须输出 `risk_resolution_plan`。

风险处理优先级固定为：

1. `WORLD_STATE_BLOCKED`
2. `STRUCTURAL_SUGGESTION_BLOCKED`
3. `hard_manual_required`
4. `risk_level: high`
5. `auto_safe_structural_fix`
6. `auto_actionable_suggestions`

`risk_resolution_plan` 必须包含：

- `mode`: `BLOCKED_WITH_REPAIR_PLAN` 或 `AUTO_FIX_THEN_REVIEW`。
- `priority_order`: 实际命中的风险类型排序。
- `immediate_action`: 当前轮应执行的动作，例如 `generate_repair_plan`、`safe_auto_fix_only`、`manual_route_required`。
- `automation_classification`: `AUTO_FIX`、`AUTO_ROUTE_COMMIT`、`AUTO_ROUTE_REVIEW` 或 `HUMAN_REQUIRED`。
- `safe_auto_fixes`: 可立即自动执行且不依赖高权限结论的建议 ID。
- `deferred_auto_fixes`: 暂缓执行的自动建议 ID，并说明被哪个高权限风险阻断。
- `required_routes`: 后续应转入的命令路由和触发条件。
- `user_decisions`: 必须由用户选择的分歧点；每项最多给 2-3 个候选方向。

推荐路由规则：

- `WORLD_STATE_BLOCKED`: 若正文证据已支撑普通状态回写，标记 `AUTO_ROUTE_COMMIT` 并进入 `更新世界` 候选提交；若正文需要依赖新的核心世界事实，标记 `AUTO_ROUTE_REVIEW`；若正文违反既有世界事实，优先重新执行 `创作第 N 章`。
- `STRUCTURAL_SUGGESTION_BLOCKED`: 若只影响未发布当前章结构，标记 `AUTO_ROUTE_COMMIT` 并重新执行 `创作第 N 章`；若影响卷目标或后续章节契约，标记 `AUTO_ROUTE_REVIEW` 并建议 `修订卷规划 ARC-001`。
- `hard_manual_required`: 必须列出候选方向和影响；只有不可逆事项才等待用户选择。
- `risk_level: high`: 可生成候选修法和影响评估，但不得提交正文或状态变更。

## 复评规则

- 复评只覆盖触发扣分或阻断的读者画像与维度。
- 复评必须重新计算聚合分，并记录哪些维度沿用首评结果。
- 复评不得扩大为全新自由审稿；若发现新引入硬伤，可记录为后续常规门禁风险，但不得开启无限评价循环。
- 自动重润色轮次必须计入章节事务的自动修正上限；超过上限时停止。
- 复评必须包含 `revision_delta`：原问题是否解决、是否引入新问题、聚合分变化、目标维度变化和保留高光是否受损。
- 若重润色解决了扣分点但磨平人物声音、情绪重量或章末钩子，必须在复评中重新扣分，不得只按原建议完成度放行。
- `PASS_WITH_AUTO_FIX` 的复评后若无新风险且分数不降，进入后续门禁；若修坏高光、引入事实风险或越权风险，转 `MANUAL_DECISION_REQUIRED`。

## 证据与引用

读者评价是必需事务证据，不写入正式 World Bible。

报告必须包含：

- 事务 ID、章节 ID、评价轮次和被评正文 hash。
- 三个读者画像的维度分、归一分、聚合分和阻断状态。
- 扣分依据、段落或场景定位、前后文摘要。
- `auto_actionable_suggestions` 和拆分后的 `manual_decision_suggestions` 清单。
- `chapter_promise`、`scene_diagnostics` 和 `likely_drop_points`。
- 多风险或阻断场景下的 `risk_resolution_plan`。
- 复评轮次的 `revision_delta`。
- `forbidden_changes`: 不得自动修改的事实、状态、设定和伏笔。
- `protected_highlights`: 高分亮点，重润色时不得误伤。
- 最终状态：`PASS`、`PASS_WITH_AUTO_FIX`、`PASS_WITH_TARGET_MISS`、`BLOCKED`、`BLOCKED_WITH_REPAIR_PLAN` 或 `MANUAL_DECISION_REQUIRED`。

短引用规则：

- 优先使用位置定位，短引只服务扣分依据。
- 每个扣分项最多 1-2 个短引。
- 单条引用不超过 40 个汉字。
- 同一评价报告累计引用不超过正文 3%。
- 禁止保存、返回或复制完整正文。

评价 artifact 建议命名：

```text
world/.transactions/<TX>/reader-evaluation-R1.md
world/.transactions/<TX>/reader-evaluation-R2.md
```

YAML 事务记录必须引用 artifact 路径、hash、轮次和最终状态。`world/chapter-summary.md` 不记录读者评价分数或报告内容。

## Worker 边界

`reader-gate-worker` 可读取完整仓库和当前 staging 正文，只能生成结构化评价证据，不得改写正文或回传完整正文。

`draft-worker` 只能消费 `auto_actionable_suggestions` 执行局部受限重润色。

`gate-worker` 继续负责后续剧情、世界观、叙事线索等语义门禁。

正式章节、World Bible、摘要、归档和事务完成状态仍只能由事务执行器提交。
