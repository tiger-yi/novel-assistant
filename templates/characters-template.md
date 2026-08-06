# 人物档案模板 (Characters Template)

**[ReAct Protocol: Characters]**
> 1. **决策摘要**: 引用 `outline.md` 中的冲突点，简述该角色在当前剧情节点的状态依据。
> 2. **Action**: 严格按照以下 schema 填入数据，禁止删除既有字段。
> 3. **Observation**: 校验该角色的境界是否与 `power.md` 中的战力梯队一致。

---

## 主角配置 (Protagonist Spec)

### 基本信息 (Main Character)
| 属性字段 (Field) | 设定值 (Value) | 备注说明 (Notes) |
| :--- | :--- | :--- |
| **人物 ID (id)** | `CHAR-YECHEN` | 创建后不可因改名或状态变化而修改 |
| **姓名 (name)** | 叶辰 | - |
| **身份 (identity)** | 家族弃子 / 剑墓传人 | 需体现社会关系与隐秘身份 |
| **境界 (realm)** | 淬体境 (九重) | 必须符合 `power.md` 定义的层级名称 |
| **所属势力 (affiliation)** | 青云城-叶家 | - |
| **性格 (personality)** | 坚毅、杀伐果断、尊师重道 | - |
| **状态 (status)** | 经脉重塑中 | 记录当前实时的负面 buff 或伤势 |

### 天赋属性 (Attributes)
| 属性字段 (Field) | 设定值 (Value) |
| :--- | :--- |
| **体质 (physique)** | 凡体 -> 荒古圣体 (未觉醒) |
| **灵魂 (soul)** | 两世为人 (灵魂力强大) |

### 功法技能 (Skills)
| 技能名称 (name) | 品阶 (grade) | 熟练度 (mastery) | 备注说明 (Notes) |
| :--- | :--- | :--- | :--- |
| 太初剑经 | 天级残篇 | 小成 | 入门/小成/大成/圆满/化境 |
| 碎石掌 | 黄级下品 | 圆满 | - |

### 人际关系 (Relationships)
| 人物 ID | 姓名 (name) | 关系 (relation) | 信任度/好感度 (trust) |
| :--- | :--- | :--- | :--- |
| `CHAR-JIANLAO` | 剑老 | 师尊 | 100 |
| `CHAR-LIURUYAN` | 柳如烟 | 死敌 (前未婚妻) | -100 |

---

## 重要配角 (Side Characters)

| 人物 ID | 姓名 (name) | 身份 (identity) | 境界 (realm) | 所属势力 (affiliation) | 与主角关系 (relation_to_mc) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CHAR-XIAOXUNER` | 萧薰儿 | 古族千金 | 灵脉境 (三重) | 神秘势力 | 青梅竹马 |
