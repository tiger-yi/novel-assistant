# 命令协议: 创作章节 (create-chapter)

> **主触发词**: `创作第 N 章`
>
> **只读预演**: `构思第 N 章`

## 功能

`创作第 N 章` 启动一次完整章节事务，按冻结的章节执行契约生成唯一执行方案，自动完成撰写、文本润色、读者评价、内容补全、验证、发布、World Bible 回写和到期归档。只有规划缺失或过期、事实冲突、逻辑死锁、无法在固定卷区间内完成卷目标、读者评价暴露结构性阻断或修订已发布章节时才暂停请求用户决策。

`构思第 N 章` 仅输出受约束执行方案和审计，不写正文、World Bible、事务记录或归档。

## 前置门禁

- 八类 World Bible 齐全，目标章节号与当前进度一致。
- `world/outline.md` 通过 `INV-PLOT-001`，目标章节所属卷已经冻结，事务记录绑定大纲和章节契约摘要。
- `writespec/style-guide.md` 必须满足 `INV-STYLE-001`，且通过 `python scripts/validate_harness.py`。
- 完整创作时，事务 preflight 必须确认 `style_basis` 字段存在且 `title` 匹配 `world/outline.md` 书名；流派、主调、金手指和核心禁忌是否仍适用，由 Agent 在重大设定变更时提供语义判断。
- 目标章节未发布；若已发布，必须得到明确修订授权并创建新的 `RNN`。
- 存在未完成的同章事务时，先按 `state-management.md` 判断恢复或创建新修订。

风格未就绪、缺少风格身份锚点或书名不匹配时必须熔断，可提示执行 `创建写作风格` 或修复现有文件，不得在章节事务中静默生成风格。

## 准备阶段

1. 由事务执行器严格解析原始命令并创建 `TX-CH-NNNN-RNN.yaml` 事务记录，记录文件基线。
2. 加载章节所需 World Bible，定位卷目标、里程碑和章节执行契约，生成一个受约束执行方案与带依据的逻辑审计。
3. 输出叙事线索处理表，逐项标明本章对活跃 `HOOK-*`、`SEED-*` 的处理动作、新候选线索、正文承载场景、预计证据和不处理理由；`构思第 N 章` 必须包含该表。
4. 审计必须证明方案保持绑定结果，且叙事线索处理不越过 `foreshadowing-spec.md` 的候选与正式状态边界；任何 `FAIL` 项不得继续。
5. 将初稿写入 `chapters/.staging/TX-CH-NNNN-RNN/CH-NNNN-标题.txt`。
6. 按 `chapter-polish.md` 执行一次纯文本润色。
7. 按 `reader-evaluation.md` 执行多读者画像评价；低于阻断线或单画像硬下限时，只能依据可自动执行建议进行局部受限重润色并复评，结构性或世界状态建议必须停止并交由人工决策。
8. 运行字数检查；低于 2300 字时只依据既有细纲补全内容，高于 2800 字时只做不改变事实的压缩，再执行一次纯文本润色，禁止新增设定或注水。
9. 对最终 staging 版本运行字数、格式、六维世界观、剧情对齐、留存结构和逻辑闭环门禁。自动修复最多 3 轮，仍失败则停止。
10. 在事务 staging 中生成 World Bible 候选文件与变更集，列出目标、实体 ID、旧值、新值、摘要和幂等键；叙事线索变更还必须列出动作、来源章节、正文证据和 `INV-FORESHADOW-001` 幂等键。此时不修改正式文件。

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
- 读者评价: 按 `reader-evaluation.md` 给出三读者画像评分、聚合分、短引证据、建议拆分、artifact 路径/hash 和最终状态；只接受 `PASS` 或 `PASS_WITH_TARGET_MISS`。
- 世界观: 按 `world-audit.md` 给出带文件、章节 ID 或实体 ID 的六维结果，其中战力满足 `INV-POWER-001`。
- 剧情对齐: 按 `INV-PLOT-001` 逐项核对事务绑定、章节结果、卷目标贡献、里程碑和未授权重大事实；不允许 `WARN` 放行。
- 状态闭环: 按 `state-management.md` 核对消耗、伤势、信息差、事务状态与幂等键；叙事线索状态满足 `INV-FORESHADOW-001`。
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
