---
schema: novel-harness/chapter-summary-template/v1
revision: 1
status: init-template
world_file: world/chapter-summary.md
template_role: init-world, rework-init-world, optimize-init-world
---

# 章节摘要

> 章节摘要是已发布正文的派生事实。初始化时保持空表；每章发布后只保留最近活跃摘要，历史摘要进入归档索引。

## 1. 活跃章节摘要

| 章节 ID | 章节 | 标题 | 时间/地点 | 视角 | 摘要正文 | 关键事件 | 主爽点类型/状态变化 | 人物状态更新 | 资源与消耗 | 伏笔与线索 | 逻辑校验 | 下一章承接 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

## 2. 最近保留策略

| 字段 | 内容 |
| :--- | :--- |
| 活跃保留范围 | 最近 3 章 |
| 归档目标 | `world/archive/chapter_summary_history.md` |
| 唯一性规则 | 同一 `CH-NNNN` 只能有一条活跃摘要 |

## 3. 已归档章节摘要索引

| 章节范围 | 摘要说明 | 归档链接 |
| :--- | :--- | :--- |
