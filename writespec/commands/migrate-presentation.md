# 命令协议: 迁移正文呈现 (migrate-presentation)

> **批次扫描触发词**: `迁移正文呈现`
>
> **授权子事务格式**: `迁移正文呈现 CH-0001`

## 功能

追溯检测已发布章节对 `INV-CHAPTER-001` 的违反，并在不改变剧情事实的前提下逐章生成等义呈现修订。批次扫描只读；正式正文及关联证据只能由获得父批次授权的单章 `TX-CH-NNNN-RNN` 子事务修改。

## 批次扫描

1. 事务执行器扫描 `chapters/` 下正式 `CH-NNNN*.txt`，忽略 staging 和非正式文件。
2. 确定性呈现扫描记录命中章节、行号、规则类别和原文命中项；Agent 另提交 `key: dialogue_clarity_scan`，绑定每个正式章节的路径/hash，并列出关键台词语义含混命中。两类均无违规的章节不进入授权集合。
3. `presentation-scan` 证据必须证明全部正式章节扫描范围完整、未解决项为空。提交前执行器复核确定性结果、章节集合、hash、行号和短引；结果变化即以 stale scan 停止。
4. 执行器把合法的确定性命中和关键台词命中合并到 `migration.chapters`。父记录完成后，该清单才是子事务授权范围；Agent 不得扩大范围，批次扫描也不得直接修改章节。

## 单章迁移

1. `迁移正文呈现 CH-NNNN` 必须引用包含该章且状态为 `COMPLETE` 的父扫描记录。
2. 事务执行器沿用该章历史最高修订号并创建下一 `TX-CH-NNNN-RNN`。
3. 内部代号优先解析 World Bible 已有显名，其次查找后续已发布正文中的稳定称谓；无法唯一解析时停止，不得临时造名。
4. staging 正文只允许删除禁用呈现、改用自然称谓或把章节引用改写为具体时间/事件承接。
5. 叙事线索摘录、摘要值和修订引用可以随等义正文同步；不得改变事件、因果、人物行为、信息差、实体关系或线索生命周期。

## 必需门禁

- `chapter-format`: 对 staging 正文重新执行完整 `INV-CHAPTER-001`。
- `presentation-equivalence`: 逐项证明新旧正文事件和事实等义，只接受 `PASS`。
- `narrative-integrity`: 证明不存在内部 ID、作者/读者/剧情安排或外部镜头调度；同时提交独立的 `key: reported_speech_audit` 与 `key: dialogue_clarity_audit`。后者必须绑定最终 staging hash，覆盖六类关键台词风险；无命中也必须提交，只接受 `PASS`。
- `plot-alignment`: 证明修订未改变已发布剧情事实，只接受 `PASS`。
- `thread-integrity`: 证明叙事线索状态和因果不变，只接受 `PASS`。
- 事务与 Postflight: 校验目标基线、正文摘要、证据引用和幂等键。

确定性违规由 Agent 结合上下文重写，最多三轮；校验器不得盲目替换。任一门禁失败只阻断该章，父批次保留已完成子事务、待处理章节和恢复点。全部授权章节完成时批次为 `COMPLETE`，否则为 `PARTIAL`。

## 写入边界

Agent 只写子事务 staging 与 YAML 证据。正式章节和 World Bible 证据目标只能由事务执行器提交。该命令不授权修改卷目标、章节事件、实体状态或未命中的其他章节。

## 相关规范

- [../chapter-creation-spec.md](../chapter-creation-spec.md)
- [../state-management.md](../state-management.md)
- [../foreshadowing-spec.md](../foreshadowing-spec.md)
