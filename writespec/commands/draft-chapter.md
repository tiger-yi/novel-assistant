# 命令协议: 创作章节 (create-chapter)

> **主触发词**: `创作第 N 章`
>
> **只读预演**: `构思第 N 章`

## 功能

`创作第 N 章` 启动一次完整章节事务，按冻结的章节执行契约生成唯一执行方案，自动完成撰写、文本润色、读者评价、内容补全、验证、发布、World Bible 回写和到期归档。阻断先按 `continuous-improvement.md` 的 `AUTO_FIX`、`AUTO_ROUTE_COMMIT`、`AUTO_ROUTE_REVIEW` 和 `HUMAN_REQUIRED` 四档处理；只有命中高风险人工边界时才暂停请求用户决策。

`构思第 N 章` 仅输出受约束执行方案和审计，不写正文、World Bible、事务记录或归档。

## 前置门禁

- 八类 World Bible 齐全，目标章节号与当前进度一致。
- `world/outline.md` 通过 `INV-PLOT-001`，目标章节所属卷已经冻结，事务记录绑定大纲和章节契约摘要。
- `writespec/style-guide.md` 必须满足 `INV-STYLE-001`，且通过 `python scripts/validate_harness.py`。
- 完整创作时，事务 preflight 必须确认 `style_basis` 字段存在且 `title` 匹配 `world/outline.md` 书名；流派、主调、金手指和核心禁忌是否仍适用，由 Agent 在重大设定变更时提供语义判断。
- 目标章节未发布时使用普通新章模式；若已发布，同一命令按 `payoff-spec.md` 进入 `published-revision` 条件模式，绑定正式正文基线、生成爽点与下游影响预览，取得明确授权后创建新的 `RNN`。不得转用 `润色章节` 规避事实变更审计。
- 新章节标题必须与已发布章节、当前活动 staging 章节和本次事务目标文件名中的标题去空白后不重名；重名时必须在准备阶段改题，不得发布。
- 存在未完成的同章事务时，先按 `state-management.md` 判断恢复或创建新修订。

风格未就绪、缺少风格身份锚点或书名不匹配时必须熔断，可提示执行 `创建写作风格` 或修复现有文件，不得在章节事务中静默生成风格。

## 准备阶段

1. 由事务执行器严格解析原始命令并创建 `TX-CH-NNNN-RNN.yaml` 事务记录，记录文件基线。
2. 加载章节所需 World Bible，定位卷目标、里程碑、章节执行契约与 `INV-PAYOFF-001` 密度档；生成受约束执行方案、爽点兑现契约与带依据的逻辑审计。旧大纲没有 `payoff_policy` 时，从非追溯启用边界起在事务 staging 建立契约，不修改既有正式 World Bible。
3. 生成章节标题并执行标题唯一性审计，列出比对范围和结论；`构思第 N 章` 必须包含候选标题及唯一性结论。
4. 输出六维世界观风险表，逐项标明体系、战力、时间、物品、地理和人物行为的本章风险、引用文件或实体、预计正文证据、需回写项和熔断项；`构思第 N 章` 必须包含该表。
5. 输出叙事线索处理表，逐项标明本章对活跃 `HOOK-*`、`SEED-*` 的处理动作、新候选线索、正文承载场景、预计证据和不处理理由；每个候选另列触发依据、功能区分、读者可见落点和范围支撑；无候选时记录原因。`构思第 N 章` 必须包含该表与候选合理性审计。
6. 审计必须证明方案保持绑定结果，标题不重名，世界观风险处理满足 `world-audit.md`，且叙事线索处理不越过 `foreshadowing-spec.md` 的候选与正式状态边界，并通过候选合理性审计；任何 `FAIL` 项不得继续。
7. 将初稿写入 `chapters/.staging/TX-CH-NNNN-RNN/CH-NNNN-标题.txt`，并按爽点契约把行动、代价、状态变化和确认落到可定位场景。
8. 按 `chapter-polish.md` 执行一次纯文本润色。
9. 按 `chapter-polish.md` 执行 `signing-first-impression-risk` 语义门禁，审查前 500-1000 字、主要场景入口和章末牵引。`WARN` 可在授权边界内自动修复并进入后续门禁；`FAIL` 必须按 L3 分层和四档自动化阻断分级进入自动修复、自动路由提交、候选复核或人工确认。
10. 按 `reader-evaluation.md` 执行多读者画像评价，记录报告路径/hash 后运行 `reader-evaluation-contract` 确定性校验；低于阻断线或单画像硬下限时，先依据可自动执行建议进行局部受限重润色并复评，结构性或世界状态建议按四档自动化阻断分级路由。校验失败不得进入后续门禁。
11. 对读者评价后的 staging 正文执行 `style-application` 语义门禁，产出至少 5 条可定位的 `style-application-evidence`，证明最终候选正文已经应用当前 `writespec/style-guide.md`。
12. 运行字数检查；低于 2300 字时只依据既有细纲补全内容，高于 2800 字时只做不改变事实的压缩，再执行一次纯文本润色，禁止新增设定或注水。
13. 对最终 staging 版本生成 `payoff-evidence.yaml`，运行 `python scripts/validate_payoff.py <payoff-evidence.yaml>`，再执行 `payoff-fulfillment` 语义门禁；随后运行字数、格式、标题唯一性、六维世界观、剧情对齐、留存结构和逻辑闭环门禁。自动修复最多 3 轮，仍失败则停止。
14. 在事务 staging 中生成 World Bible 候选文件与变更集，列出目标、实体 ID、旧值、新值、摘要和幂等键；世界观相关变更必须列出六维审计结论、来源章节、引用文件或实体 ID 和正文证据，其中战力结论必须显式满足 `INV-POWER-001`；叙事线索变更还必须列出动作、来源章节、正文证据和 `INV-FORESHADOW-001` 幂等键。此时不修改正式文件。

整个准备阶段必须遵守 `INV-TRANSACTION-001`。

## 提交阶段

1. 事务执行器确认必需 pipeline 阶段、门禁、语义证据与全部目标基线通过。
2. 事务执行器发布最终 staging 正文，并按 `INV-STATE-001` 顺序应用 World Bible 候选文件。
3. 事务执行器核对正式目标摘要、跨文件引用和幂等键，原子更新 YAML 恢复点。
4. 按 `INV-ARCHIVE-001` 判断条件归档；迁移仍只能由事务执行器执行，歧义时记录待处理状态。

提交阶段意外中断时不得静默回滚用户文件。记录最后成功步骤、已修改文件和恢复点，事务状态保持非 `COMPLETE`。

## 门禁

- 字数: `python scripts/check_count.py <chapter_file> --target 2300 --max 2800 --segments`
- 格式: `python scripts/validate_chapter.py <chapter_file> --target 2300 --max 2800`，必须满足 `INV-CHAPTER-001`。
- 签约首感风险: 按 `chapter-polish.md` 给出 `signing_first_impression_risk` 证据，覆盖开篇、主要场景入口和章末牵引；接受 `PASS` 或 `WARN` 继续。`FAIL` 时不得发布当前失败正文，`L3-SAFE` 可自动修复，`L3-ROUTE-AUTO` 默认进入 `AUTO_ROUTE_COMMIT` 生成并验证单章候选后由事务执行器提交；若影响卷目标、后续契约、World Bible 核心事实或已发布事实，则降级为 `AUTO_ROUTE_REVIEW` 或 `HUMAN_REQUIRED`。
- 读者评价: 按 `reader-evaluation.md` 给出三读者画像评分、聚合分、短引证据、建议拆分、独立的 `dialogue_clarity_cross_check`、artifact 路径/hash 和最终状态；随后运行 `python scripts/validate_reader_evaluation.py <reader_evaluation_file>`。交叉复核的外部补释依赖或审计冲突必须为空，只接受 `PASS`、`PASS_WITH_AUTO_FIX` 或 `PASS_WITH_TARGET_MISS`。
- 爽点兑现: 按 `payoff-spec.md` 提交 `payoff_fulfillment_evidence`，确定性校验结构、密度档、类型轮换和滚动窗口，语义门禁核对正文证据；只接受 `PASS`。需要新增行动或状态变化时必须退出润色并按自动化阻断分级路由。
- 风格应用: 按 `style-guide.md` 给出至少 5 条可定位证据，覆盖核心调性、受限视角/认知偏差、人物声线、节奏或爽点结构、题材质感/黑名单规避；优先引用正文行号，行号不稳定时使用场景和段落摘要。只接受 `PASS`。失败时只允许文本润色或局部呈现重写，不得改变剧情事实、人物决策、胜负、伤势、资源、伏笔状态或 World Bible。
- 叙事完整性: 按 `chapter-creation-spec.md` 扫描全部在场台词与非在场引述，并独立执行关键台词风险扫描；提交 `key: reported_speech_audit` 与 `key: dialogue_clarity_audit`。后者必须绑定最终 staging hash，覆盖六类风险、关键台词语义与未解决项；零命中仍提交完整证据，且只接受 `PASS`。
- 世界观: 按 `world-audit.md` 给出带文件、章节 ID 或实体 ID 的六维结果，其中战力满足 `INV-POWER-001`。
- 剧情对齐: 按 `INV-PLOT-001` 逐项核对事务绑定、章节结果、卷目标贡献、里程碑和未授权重大事实；不允许 `WARN` 放行。
- 状态闭环: 按 `state-management.md` 核对消耗、伤势、信息差、事务状态与幂等键；叙事线索状态满足 `INV-FORESHADOW-001`。
- 叙事线索完整性: 按 `foreshadowing-spec.md` 提交 `narrative_thread_handling_table`、`active_thread_due_audit`、`candidate_thread_rationale` 与 `foreshadowing_change_set_evidence`；候选合理性必须为 `PASS`，无候选或无正式变更也必须提供相应的检查结论。

## 已发布目标条件模式

`创作第 N 章` 命中已发布目标时不新增命令路由。执行器必须记录 `mode: published-revision`、原文 hash、事实差异、下游影响和确认状态。影响未发布后续契约时生成 `修订卷规划 ARC-NNN` 候选并等待确认；影响其他已发布章节时列出连续返工范围并停止单章提交。没有 `approval_status: approved` 的爽点证据不得进入 commit。
- 周期原创性: 初始化大纲后、每 10 章、卷结束或核心设定变更时执行完整审计；单章只扫描套路黑名单。

## 完成输出

报告事务 ID、绑定的大纲修订与卷 ID、正式章节、修改的 World Bible 文件、门禁结果和归档结果。归档歧义必须单列为待处理项，不得把已成功提交的章节描述为完全失败。

## 相关规范

- [../chapter-creation-spec.md](../chapter-creation-spec.md)
- [../chapter-polish.md](../chapter-polish.md)
- [../reader-evaluation.md](../reader-evaluation.md)
- [../state-management.md](../state-management.md)
- [../foreshadowing-spec.md](../foreshadowing-spec.md)
- [../world-audit.md](../world-audit.md)
- [../archiving-spec.md](../archiving-spec.md)
