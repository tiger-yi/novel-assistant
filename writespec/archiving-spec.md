# World Bible 归档执行规范 (Archiving Rules)

## 1. 触发判定
- **卷终(Arc Complete)**: `outline.md` 中某卷标记为 `[已完成]`。
- **周期(Cycle)**: 连续创作超过 10 章未进行归档。
- **强制(Manual)**: 用户输入 `归档世界观`。

## 2. 细则说明
- **outline.md**: 将已完成卷的“详细章节规划表”剪切至 `archive/outline_history.md`，主文件仅保留该卷的“一句话梗概”。
- **characters.toml**: 将 `status` 为“已死亡”、“已消失”或“长期离场”的角色迁移至 `archive/characters_registry.toml`。
- **timeline.md**: 将当前卷之前的琐碎事件（非里程碑）迁移至 `archive/timeline_chronicles.md`。
- **inventory.md**: 将“已消耗”、“已损毁”、“已遗弃”的道具迁移至 `archive/inventory_logs.md`。
- **geography.md**: 将主角已离开且无后续伏笔（伏笔数=0）的旧地图详情迁移至 `archive/world_atlas.md`。
