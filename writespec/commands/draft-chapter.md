# 命令协议: 创作章节 (create-chapter)

> **主触发词**: `创作第 N 章`
>
> **只读预演**: `构思第 N 章`

## 功能

`创作第 N 章` 启动一次完整章节事务，自动完成构思、采用推荐分支、撰写、文本润色、内容补全、验证、发布、World Bible 回写和到期归档。只有事实冲突、逻辑死锁或修订已发布章节时才暂停请求用户决策。

`构思第 N 章` 仅输出细纲、推荐分支和审计，不写正文、World Bible、事务记录或归档。

## 前置门禁

- 八类 World Bible 齐全，目标章节号与当前进度一致。
- `writespec/style-guide.md` 必须满足 `INV-STYLE-001`，且通过 `python scripts/validate_harness.py`。
- 目标章节未发布；若已发布，必须得到明确修订授权并创建新的 `RNN`。
- 存在未完成的同章事务时，先按 `state-management.md` 判断恢复或创建新修订。

风格未就绪时必须熔断，可提示执行 `创建写作风格` 或修复现有文件，不得在章节事务中静默生成风格。

## 准备阶段

1. 由事务执行器严格解析原始命令并创建 `TX-CH-NNNN-RNN.yaml` 事务记录，记录文件基线。
2. 加载章节所需 World Bible，生成细纲、2-3 个候选分支和带依据的逻辑审计。
3. 审计通过后自动采用推荐分支；任何 ❌ 项不得继续。
4. 将初稿写入 `chapters/.staging/TX-CH-NNNN-RNN/CH-NNNN-标题.txt`。
5. 按 `chapter-polish.md` 执行一次纯文本润色。
6. 运行字数检查；不足 2000 字时只依据既有细纲补全内容，再执行一次纯文本润色，禁止新增设定或注水。
7. 对最终 staging 版本运行字数、格式、六维世界观和逻辑闭环门禁。自动修复最多 3 轮，仍失败则停止。
8. 在事务 staging 中生成 World Bible 候选文件与变更集，列出目标、实体 ID、旧值、新值、摘要和幂等键；此时不修改正式文件。

整个准备阶段必须遵守 `INV-TRANSACTION-001`。

## 提交阶段

1. 事务执行器确认必需 pipeline 阶段、门禁、语义证据与全部目标基线通过。
2. 事务执行器发布最终 staging 正文，并按 `INV-STATE-001` 顺序应用 World Bible 候选文件。
3. 事务执行器核对正式目标摘要、跨文件引用和幂等键，原子更新 YAML 恢复点。
4. 按 `INV-ARCHIVE-001` 判断条件归档；迁移仍只能由事务执行器执行，歧义时记录待处理状态。

提交阶段意外中断时不得静默回滚用户文件。记录最后成功步骤、已修改文件和恢复点，事务状态保持非 `COMPLETE`。

## 门禁

- 字数: `python scripts/check_count.py <chapter_file> --target 2000 --segments`
- 格式: `python scripts/validate_chapter.py <chapter_file> --target 2000`，必须满足 `INV-CHAPTER-001`。
- 世界观: 按 `world-audit.md` 给出带文件、章节 ID 或实体 ID 的六维结果，其中战力满足 `INV-POWER-001`。
- 状态闭环: 按 `state-management.md` 核对消耗、伤势、信息差、事务状态与幂等键；叙事线索状态满足 `INV-FORESHADOW-001`。
- 周期原创性: 初始化大纲后、每 10 章、卷结束或核心设定变更时执行完整审计；单章只扫描套路黑名单。

## 完成输出

报告事务 ID、推荐分支、正式章节、修改的 World Bible 文件、门禁结果和归档结果。归档歧义必须单列为待处理项，不得把已成功提交的章节描述为完全失败。

## 相关规范

- [../chapter-creation-spec.md](../chapter-creation-spec.md)
- [../chapter-polish.md](../chapter-polish.md)
- [../state-management.md](../state-management.md)
- [../foreshadowing-spec.md](../foreshadowing-spec.md)
- [../world-audit.md](../world-audit.md)
- [../archiving-spec.md](../archiving-spec.md)
