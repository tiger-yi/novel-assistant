---
name: novel-metadata-generator
description: Generate compliant novel metadata (title, summary, tags, cover prompt) based on world/outline.md. Use when initializing a novel project or preparing for publication.
---

# Novel Metadata Generator

该技能用于根据 `world/outline.md` 自动生成符合平台规范的小说元数据（书名、简介、标签、封面提示词）。

## 核心输入 (Inputs)
- **大纲**: `world/outline.md`
- **规则**: `references/platform-rules.md` (字数/禁忌)
- **标签**: `references/tag-options.md` (分类/标签库)

## 核心输出 (Outputs)
- **元数据文件**: `metadata/novel-metadata.md` (覆盖更新)

## 执行流程 (Workflow)

1.  **读取大纲**: 读取 `world/outline.md` 获取核心设定（梗、金手指、主角、剧情）。
2.  **加载规则**: 读取 `references/platform-rules.md` 获取平台限制。
3.  **加载标签**: 读取 `references/tag-options.md` 获取可选标签。
4.  **生成方案**: 基于大纲和规则，生成 **5 套** 完整的元数据方案。
    - **书名**: <15字，吸睛，符合平台风格。
    - **简介**: 50-500字，突出“黄金三章”爽点与悬念。
    - **标签**: 1个主分类 + 2套副标签（主题/角色/情节各2个）。
    - **封面提示词**: 遵循 **ReAct 封面构思协议** 生成 Midjourney 提示词。
5.  **归档结果**: 将生成的所有方案保存至 `metadata/novel-metadata.md`。

## ReAct 封面构思协议 (Cover Design Protocol)

在生成封面提示词前，必须执行以下 **Thought** 过程：

1.  **意境分析**: 确定书名氛围（霸气/诡秘/仙气）。
2.  **角色特征**: 提取主角视觉元素（发色/服饰/武器）。
3.  **视觉钩子**: 选定一个具象的冲突符号（如：破碎的玉佩、燃烧的剑）。
4.  **构图规划**: 选择构图（如：黄金分割、对角线）与视角（如：俯视、特写）。
5.  **参数设定**: `--ar 3:4 --v 6.0 --niji 6`。
6.  **提示词结构**: `[核心主体] + [视觉钩子] + [场景与背景] + [构图与视角] + [材质与渲染] + [艺术风格] + [中文排版声明] + --ar 3:4 --v 6.0 --niji 6`


## Midjourney 提示词模板 (Prompt Template)

生成提示词时，必须严格遵循以下结构：

```text
[核心主体] + [视觉钩子] + [场景与背景] + [构图与视角] + [材质与渲染] + [艺术风格] + [中文排版声明] + --ar 3:4 --v 6.0 --niji 6
```

## 📋 构图与排版说明
- **构图风格**: [如：黄金分割, 赛博朋克审美, 视觉冲突钩子]
- **排版建议**: 在顶部中央为书名 **[作品名称]** 预留空间，在右下角为作者 **[作者笔名]** 预留空间。确保最终作品中不出现英文文字。

**示例**:
> 一位平静的年轻修仙者，盘腿冥想(主体)，额头散发出蓝色全息数据流(视觉钩子)，雄伟的悬浮山脉背景(场景)，黄金分割构图(构图)，8k分辨率(材质)，东方古典与赛博朋克融合(风格)，在顶部中央为书名 **[作品名称]** 预留空间，在右下角为作者 **[作者笔名]** 预留空间 --ar 3:4 --v 6.0 --niji 6

