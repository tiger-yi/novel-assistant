# Novel Assistant (AI小说写作助手)

Novel Assistant 是一个用于辅助创作中文玄幻小说的结构化世界观数据库管理项目。项目旨在通过结构化的数据文件（World Bible）来维护长篇玄幻小说的剧情、人物、时间线、道具和地理信息，确保长篇作品的世界观一致性和逻辑连贯性。

## 核心指令集 (Key Commands)

### 1. "初始化世界" (Initialize World)
从零构建世界观

方式一:
直接输入指令:
```markdow
初始化世界

```
方式二:
直接输入指令+信息:
```markdow
初始化世界 主题+剧情+风格等信息

```

### 2. "更新世界" (Update World)
分析最近生成的正文，同步更新所有 World Bible 文件（人物、物品、地理、时间线等）。
**注意**：此指令会自动触发 `chapter-polisher` 对新章节进行润色和质量检查。

直接输入指令:
```markdow
更新世界

```
### 3. "构思章节" (Draft Chapter)
启动单章创作的标准 ReAct 工作流：
1.  **构思 (Plan)**：检索世界观，生成场景细纲。
2.  **撰写 (Draft)**：根据细纲撰写正文。
3.  **收尾 (Finish)**：提示用户更新世界。

直接输入指令:
```markdow
构思章节 1
构思章节 2

```

### 4. "归档世界" (Archive World)
强制扫描并清理 `world/` 目录，将已完成的剧情、死亡人物、消耗道具迁移至 `world/archive/`。

直接输入指令:
```markdow
归档世界

```

### 5. "查看世界状态" (Check World Status)
返回当前时间点、主角所在地、当前状态（HP/MP/Buff）、最近的主线任务目标。

直接输入指令:
```markdow
查看世界状态

```

## 技能
技能在skills目录下解压放入AI工具的skills目录下
### chapter-polisher
一个复合技能，循环执行字数检查、内容扩充和去除 AI 味，直到章节在满足长度要求的同时保持高质量。

### Novel Metadata Generator
为玄幻小说生成符合平台规则的元数据（书名、标签、主角名、简介、封面提示词）。基于 world\outline.md 的内容，并严格遵守 references\platform-rules.md 中的字数和内容限制，从 references\tag-options.md 中选择合适的标签。
* **书名**:开新书时选择一个填写即可
* **标签**:开新书时按照填写即可
* **主角名**:开新书时按照填写即可
* **简介**:开新书时按照填写即可
* **封面提示词**:将提示词输入元宝生成小说封面


## 指令使用流程

> STEP 1:
    初始化世界

> STEP 2:
   构思章节 1
   
> STEP 3:
   更新世界

> STEP 4:
   构思章节 2

> STEP 5:
   更新世界
   
> STEP 6:
   循环2-3步骤


