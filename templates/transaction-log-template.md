# 章节事务日志

| 字段 | 值 |
| :--- | :--- |
| 事务 ID | `TX-CH-NNNN-RNN` |
| 章节 ID | `CH-NNNN` |
| 修订序号 | `RNN` |
| 采用分支 | [推荐分支名称] |
| 主体状态 | `PREFLIGHT/PREPARING/PREPARED/COMMITTING/COMPLETE/FAILED` |
| 归档子状态 | `NOT_CHECKED/NOT_DUE/COMPLETE/ARCHIVE_PENDING` |
| 最后成功步骤 | [步骤名称] |
| staging 内容摘要 | [摘要算法与值] |

## 文件基线

记录事务开始时目标章节、八类 World Bible、相关归档目标和已有未提交差异。不得保存 secrets。

## 准备阶段

| 步骤 | 结果 | 验证证据 |
| :--- | :--- | :--- |
| Preflight | [PASS/FAIL] | [风格/Bible/章节/事务] |
| Plan | [PASS/FAIL] | [推荐分支/逻辑审计] |
| Stage | [PASS/FAIL] | [staging 文件] |
| Text Polish | [PASS/FAIL] | [调整摘要] |
| Final Gates | [PASS/FAIL] | [命令/六维证据] |
| Prepare Change Set | [PASS/FAIL] | [变更集/冲突] |

## World Bible 变更集

| 文件 | 实体 ID | 字段/动作 | 旧值摘要 | 新值摘要 | 来源章节 | 幂等键 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [文件] | [ID] | [新增/修改/扣减/回收] | [旧值] | [新值] | `CH-NNNN` | [键] |

## 提交阶段

| 步骤 | 结果 | 验证证据 |
| :--- | :--- | :--- |
| Publish | [PASS/FAIL] | [正式章节/内容摘要] |
| State Update | [PASS/FAIL] | [修改文件/幂等键] |
| Postflight | [PASS/FAIL] | [正文一致性/引用/闭环] |
| Conditional Archive | [NOT_DUE/PASS/PENDING] | [预览/迁移/歧义] |

## 恢复点

记录已生效步骤、已修改文件、未执行步骤及下一次恢复前必须复核的内容摘要和幂等键。禁止整文件回滚用户原有差异。
