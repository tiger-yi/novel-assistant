# World Bible 归档执行规范 (Archiving Rules)

## 1. 触发判定
- **卷终(Arc Complete)**: `outline.md` 中某卷标记为 `[已完成]`。
- **周期(Cycle)**: 每满 10 章进行一次归档；不足 10 章不归档。
- **强制(Manual)**: 用户输入 `归档世界观`。

## 2. 细则说明
- **outline.md**: 将已完成的“10 章块”或“完整卷”的详细章节规划表剪切至 `archive/outline_history.md`；主文件仅保留进行中部分的详细表，并对已归档部分仅保留“一句话梗概+存档链接”。
- **outline.md（悬念与线索管理）**: 将“悬念与线索管理”中标记为 `[x]` 的伏笔条目视为“已回收”，统一迁移至 `archive/outline_history.md` 的“伏笔回收”分区；主文件仅保留该伏笔的“一句话结论+归档链接”。归档记录建议格式：`[伏笔ID] 标题 | 埋设章节 -> 回收章节 | 证据要点 | 相关章节链接`。
- **characters.toml**: 将 `status` 为“已死亡”、“已消失”或“长期离场”的角色迁移至 `archive/characters_registry.toml`。
- **timeline.md**: 将当前卷之前的琐碎事件（非里程碑）迁移至 `archive/timeline_chronicles.md`。
- **inventory.md**: 将“已消耗”、“已损毁”、“已遗弃”的道具迁移至 `archive/inventory_logs.md`。
- **geography.md**: 将主角已离开且无后续伏笔（伏笔数=0）的旧地图详情迁移至 `archive/world_atlas.md`。
