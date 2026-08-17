# 命令协议: 查看世界状态 (check-status)

> **触发词**: "查看世界状态"

## 功能
快速状态查询。

## 输出 (Output)
返回:
- **当前时间点**: 当前纪元/年份/日期。
- **主角所在地**: 当前位置 (地理坐标/区域)。
- **当前状态**: 境界、伤势、已记录状态与资源；不生成 World Bible 未定义的数值。
- **最近的主线任务目标**: 当前推进的 mainline 目标。
- **事务缓存**: 四类 staging 的总字节数、已满足 10 天的可清理项与字节数、活动事务数和孤儿目录数；只报告当前状态，不写首次观察时间。

## 执行流程
1. 读取 `world/.transactions/*.yaml`，报告未完成事务、最后成功阶段与恢复点；不存在时标记“无活动事务”。
2. 读取 `world/timeline.md` 获取当前时间点。
3. 读取 `world/characters.md` 获取主角身份、境界、伤势和状态。
4. 读取 `world/geography.md` 核验主角所在地与区域状态。
5. 读取 `world/inventory.md` 汇总当前资源，不凭空生成 HP/MP 数值。
6. 读取 `world/outline.md` 获取最近主线任务目标。
7. 只读扫描 `chapters/.staging/`、`world/.staging/`、`analysis/.staging/`、`metadata/.staging/` 与事务 YAML，汇总缓存指标；历史事务或孤儿目录尚无本地观察时间时标记为不可清理，不创建观察记录。
8. 汇总输出并为每项标注来源文件；字段不存在时输出“未记录”。本命令只读，不创建事务。

## 相关规范
- 时间线: `world/timeline.md`
