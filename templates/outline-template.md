---
schema: novel-harness/outline/v2
revision: 1
status: frozen
current_arc: ARC-001
world_file: world/outline.md
template_role: init-world, rework-init-world, optimize-init-world
novel_goal: "[全书最终可验证结果]"
story_force:
  protagonist: "[核心视角人物]"
  active_goal: "[主角主动目标]"
  theme_lens: "[反复验证的问题或价值冲突]"
  conflict_engine: "[目标与阻力的持续对抗关系]"
  reversal_promise: "[主线或卷级反转承诺]"
volumes:
  - id: ARC-001
    title: "[第一卷卷名]"
    start_chapter: 1
    end_chapter: 3
    planning_status: frozen
    entry_cause: "[故事开端或上一卷形成的进入原因]"
    goal:
      id: GOAL-ARC-001
      result: "[本卷结束时必须形成的可验证终态]"
      completion_conditions:
        - "[完成条件]"
      required_causality:
        - "[必须保留的因果链]"
      forbidden_outcomes:
        - "[禁止采用的结果或捷径]"
      completion_evidence: "[卷终正文、章节摘要及实体证据]"
    milestones:
      - id: MS-ARC-001-01
        due_chapter: 1
        outcome: "[建立卷冲突]"
      - id: MS-ARC-001-02
        due_chapter: 2
        outcome: "[取得关键条件]"
      - id: MS-ARC-001-03
        due_chapter: 3
        outcome: "[完成卷目标]"
    chapters:
      - id: CH-0001
        task: "[本章必须完成的任务]"
        preconditions:
          - "[前置状态]"
        conflict: "[核心冲突]"
        outcome: "[可验证结果变化]"
        arc_contribution: "[对卷目标的具体贡献]"
        closing_pull: "[服务主线的章末牵引]"
        milestone: MS-ARC-001-01
        golden_three_role: inciting
        status: planned
      - id: CH-0002
        task: "[本章必须完成的任务]"
        preconditions:
          - "[前置状态]"
        conflict: "[核心冲突]"
        outcome: "[可验证结果变化]"
        arc_contribution: "[对卷目标的具体贡献]"
        closing_pull: "[服务主线的章末牵引]"
        milestone: MS-ARC-001-02
        golden_three_role: feedback
        status: planned
      - id: CH-0003
        task: "[本章必须完成的任务]"
        preconditions:
          - "[前置状态]"
        conflict: "[核心冲突]"
        outcome: "[可验证结果变化]"
        arc_contribution: "[对卷目标的具体贡献]"
        closing_pull: "[服务主线的章末牵引]"
        milestone: MS-ARC-001-03
        golden_three_role: goal-lock
        status: planned
  - id: ARC-002
    title: "[第二卷卷名]"
    start_chapter: 4
    end_chapter: 6
    planning_status: roadmap
    entry_cause: "[第一卷终态如何导致第二卷]"
    goal:
      id: GOAL-ARC-002
      result: "[第二卷可验证终态]"
      completion_conditions:
        - "[完成条件]"
      required_causality:
        - "[必须承接的卷间因果]"
      forbidden_outcomes:
        - "[禁止结果]"
      completion_evidence: "[卷终证据]"
    milestones: []
    chapters: []
---

# [小说名称] 创作大纲

> YAML frontmatter 是卷路线图和章节执行契约的机器权威；下方内容是人类可读规划视图，生成或修订时必须与 frontmatter 同步。

## 1. 基本信息

| 字段 | 内容 |
| :--- | :--- |
| 书名 |  |
| 题材类型 |  |
| 题材赛道 |  |
| 情绪闭环 |  |
| 主题透镜 |  |
| 核心视角人物 |  |
| 主角主动目标 |  |
| 核心冲突引擎 |  |
| 核心梗 |  |
| 金手指/核心卖点 |  |
| 平衡机制 |  |
| 主线反转承诺 |  |
| 预计总字数 |  |
| 单章目标字数 |  |
| 目标受众 |  |

## 2. 故事力基线

| 维度 | 初始化答案 | 关联证据文件 |
| :--- | :--- | :--- |
| 人物驱动 |  | `characters.md` |
| 主题透镜 |  | `outline.md` |
| 内心冲突 |  | `characters.md` / `outline.md` |
| 人物冲突 |  | `characters.md` / `geography.md` |
| 外部冲突 |  | `geography.md` / `timeline.md` / `inventory.md` |
| 情理内反转 |  | `hooks.md` |
| 角色功能收束 |  | `characters.md` / `geography.md` |

## 3. 全书结构

| 阶段 | 章节范围 | 核心功能 | 必达结果 |
| :--- | :--- | :--- | :--- |
| 第一幕 |  |  |  |
| 第二幕 |  |  |  |
| 第三幕 |  |  |  |

## 4. 黄金三章与分卷循环

| 章节/阶段 | 节奏角色 | 主角行动 | 冲突变化 | 代价/反馈 | 必达内容 | 章末牵引 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 开篇/切入 | inciting |  |  |  |  |  |
| 发展/反馈 | feedback |  |  |  |  |  |
| 目标锁死 | goal-lock |  |  |  |  |  |

## 5. 分卷路线图

| 卷 ID | 固定章节区间 | 卷目标 ID | 可验证终态 | 规划状态 |
| :--- | :--- | :--- | :--- | :--- |
| `ARC-001` | `CH-0001..CH-0003` | `GOAL-ARC-001` |  | frozen |
| `ARC-002` | `CH-0004..CH-0006` | `GOAL-ARC-002` |  | roadmap |

## 6. 章节执行契约

| 章节 ID | 所属卷 | 章节任务 | 前置状态 | 主角主动选择 | 核心冲突 | 结果变化 | 卷目标贡献 | 章末牵引 | 里程碑 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CH-0001` | `ARC-001` |  |  |  |  |  |  |  | `MS-ARC-001-01` | planned |
| `CH-0002` | `ARC-001` |  |  |  |  |  |  |  | `MS-ARC-001-02` | planned |
| `CH-0003` | `ARC-001` |  |  |  |  |  |  |  | `MS-ARC-001-03` | planned |

## 7. 情绪爆发点规划

| 事件 ID | 预计章节/范围 | 爆发点描述 | 情绪类型 | 爽感来源 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |

## 8. 反转与误导规划

| 反转 ID | 层级 | 铺垫位置 | 表面误导 | 真实指向 | 触发条件 | 预计回收范围 | 关联线索 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |

## 9. 核心设定摘要

| 维度 | 核心内容 | 关联文件 |
| :--- | :--- | :--- |
| 核心冲突 |  |  |
| 主角初始处境 |  | `characters.md` |
| 力量体系摘要 |  | `power.md` |
| 地理与势力格局 |  | `geography.md` |
| 关键资源/道具 |  | `inventory.md` |
| 长线叙事线索 |  | `hooks.md` |

## 10. 创作统计

| 字段 | 当前值 |
| :--- | :--- |
| 已完成章节数 | 0 |
| 累计字数 | 0 |
| 当前完成进度 | 0% |
