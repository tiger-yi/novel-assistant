# 长篇状态管理规范 (State Management)

本规范定义事实权威、稳定标识、两阶段章节事务、幂等恢复与归档检索。任何同时涉及章节和 World Bible 的流程必须加载本规范。

## 1. 事实职责与优先级

冲突时按以下顺序判断证据权威，但不得静默覆盖低优先级来源：

1. 用户在当前任务中明确批准的修订。
2. 已发布章节中已经发生的事件。
3. 活跃 World Bible 中的当前状态。
4. `world/archive/` 中的历史状态。
5. `outline.md` 中尚未发生的未来规划。
6. `chapter-summary.md` 等派生摘要。

正文记录已发生事实，World Bible 记录当前规范化状态，大纲记录未来意图，摘要只用于检索。冲突时输出文件、实体 ID、字段和建议处理方式，未经授权不得重写已发布章节。

## 2. 稳定标识

| 类型 | 格式 | 示例 |
| :--- | :--- | :--- |
| 章节 | `CH-NNNN` | `CH-0008` |
| 人物 | `CHAR-SLUG` | `CHAR-LINCHEN` |
| 物品/功法 | `ITEM-SLUG` | `ITEM-QINGFU` |
| 地点/势力 | `LOC-SLUG` / `FAC-SLUG` | `LOC-QINGYUN` |
| 悬念钩子 | `HOOK-NNNN` | `HOOK-0012` |
| 伏笔 | `SEED-NNNN` | `SEED-0012` |
| 时间事件 | `EVT-NNNN` | `EVT-0041` |

ID 创建后不可因改名或状态变化而修改。顺序型 ID 取全部活跃与归档记录的历史最大编号加一，删除或归档后的编号不得复用。

## 3. 章节事务

每次完整创作使用 `TX-CH-NNNN-RNN`。首次发布为 `R01`；同章修订或采用新方案时递增。唯一机器事实写入 `world/.transactions/TX-CH-NNNN-RNN.yaml`，使用 `novel-harness/transaction/v1`；不得维护 Markdown 状态副本。

### INV-TRANSACTION-001 写入隔离

`构思第 N 章` 不得创建事务或修改文件；完整创作的准备阶段只允许写 staging 正文、staging World Bible 候选与 YAML 事务记录，不得修改正式章节或 World Bible。正式目标只能由事务执行器写入。违反任一边界必须停止，不能以之后回滚代替隔离。

### 3.1 准备阶段

准备阶段允许写 staging 正文、候选状态文件和 YAML 事务记录，不得修改正式章节或 World Bible：

1. **Preflight**：校验风格就绪、八类 Bible、章节序号、已发布状态和未完成事务。
2. **Plan**：生成候选分支，逻辑审计通过后自动采用推荐分支。
3. **Stage**：写入 `chapters/.staging/TX-CH-NNNN-RNN/CH-NNNN-标题.txt`；所有候选文件路径必须同时包含 `.staging` 和事务 ID。
4. **Text Polish**：执行纯文本润色；不足字数时补全后再次润色。
5. **Final Gates**：对最终 staging 版本运行字数、格式、六维审计和逻辑闭环。
6. **Prepare Change Set**：生成 World Bible 变更集，记录实体 ID、旧值、新值、来源章节和幂等键。

任一门禁失败或变更集存在事实冲突时停止，不进入提交阶段。
确定性门禁的 `PASS` 只能由事务执行器实际运行 Manifest 登记命令后写入，事务 YAML 中预填的状态不具有效力。普通写命令的空变更集不得标记完成；只读审计记录和 `archive_state: NOT_DUE` 的独立归档除外。

### 3.2 提交阶段

1. **Publish**：事务执行器校验全部基线后，将已验证 staging 内容发布为正式章节并记录摘要值。
2. **State Update**：事务执行器按 `INV-STATE-001` 应用已准备的候选文件，每个成功步骤原子记录幂等键。
3. **Postflight**：核对正式正文与 staging 摘要一致、本地 Markdown 行内/引用式链接的文件与锚点存在、状态变更完整且幂等键唯一；跨文件事实关系由对应语义门禁提供证据。
4. **Conditional Archive**：判断归档到期；无歧义时由事务执行器执行，有歧义时记录 `ARCHIVE_PENDING`。

只有 Publish、State Update 和 Postflight 全部通过，章节主体事务才为 `COMPLETE`。归档歧义不撤销章节完成状态，但必须作为待处理子状态报告。

### 3.3 中断与恢复

仓库可能包含用户未提交修改，失败时禁止整文件回滚。YAML 事务记录必须保存最后成功步骤、已修改文件、未执行步骤和恢复点。只有继续相同推荐分支与变更集时恢复原事务，否则创建下一修订序号。

提交阶段中断时，先依据内容摘要值、章节 ID 和幂等键判定哪些步骤已经生效，再补做未完成步骤，禁止重复扣减或追加。
若正式目标已等于 staging 摘要而幂等键尚未落盘，执行器将其识别为“替换已完成、记账未完成”，先补记幂等键再继续恢复。

### 3.4 授权与周期记录

Manifest 声明 `requires_confirmation: when_overwriting` 时，每个被覆盖目标都必须通过 `novel_harness.py confirm-overwrite` 的交互操作确认。确认记录由事务 nonce、规范化目标路径和基线摘要绑定，手写 `source: user` 或通配目标均无效。该机制是 Harness 内的操作授权边界，不等同于操作系统身份认证。

`审计原创性` 虽不修改正式内容，仍由执行器创建 YAML 执行记录。记录的 `coverage.through_chapter` 取开始审计时最高已完成章节，`coverage.events` 绑定当时全部未覆盖周期事件事务 ID；提交时重新计算，不一致即拒绝。周期门禁要求第 11、21 等下一周期章节开始前，存在覆盖上一边界及全部事件且状态为 `COMPLETE` 的原创性审计记录。

## 4. 幂等规则

### INV-STATE-001 有序幂等回写

World Bible 变更集必须按 `chapter-summary -> characters -> inventory -> timeline -> geography -> power -> hooks -> outline` 顺序应用，并以稳定章节/事件/实体 ID 和变更来源判重。恢复或重复执行不得重复追加、扣减或创建等价状态。

- 同一 `CH-NNNN` 只能有一条活跃章节摘要。
- 时间事件以 `EVT-* + CH-*` 判重。
- 道具变更必须记录来源章节和变更 ID，恢复时不得重复扣减。
- 叙事线索状态变更按 `INV-FORESHADOW-001` 以 `HOOK-*` 或 `SEED-* + 动作 + CH-*` 判重。
- 归档以实体 ID 或章节区间判重；目标已存在时只修复索引。

悬念钩子与伏笔的合法前置状态和证据要求由 `foreshadowing-spec.md` 定义；本规范只负责按已准备变更集有序应用。

## 5. 长上下文检索

默认读取 Manifest 中匹配任务模式的 profile。只有活跃文件含归档链接、实体状态只存在于归档、或任务涉及跨卷因果和事实争议时，才按实体 ID、章节 ID 或章节区间加载最小归档片段。找不到依据时不得用模型记忆补全。

## 6. 输出与门禁

对外只报告决策摘要、文件证据和风险，不输出完整内部推理链。

- 确定性门禁由脚本退出码判定，结果写入 YAML 事务记录。
- 语义门禁必须逐维提供结论、来源文件、章节 ID 或实体 ID；引用正文时记录摘要值。
- 门禁统一返回 `PASS`、`WARN`、`FAIL` 或附原因的 `NOT_APPLICABLE`；必需结果或证据缺失按 `FAIL`。
- 准备阶段失败不得发布或回写。
- 提交阶段失败不得声称事务完成，必须给出恢复点。
