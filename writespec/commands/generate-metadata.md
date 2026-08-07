# 命令协议: 生成小说元数据 (generate-metadata)

## 功能

`生成小说元数据` 根据当前大纲生成五套书名、简介、标签与封面提示词方案。

## 命令契约

- **生效入口**: `command`
- **准备写入**: `metadata/.staging/<transaction-id>/novel-metadata.md`
- **正式目标**: `metadata/novel-metadata.md`
- **覆盖授权**: 正式目标已存在时必须先展示变更范围并取得用户确认。
- **唯一写入口**: Agent 只生成 staging 文件；正式目标只能由事务执行器发布。

## 执行流程

1. 事务执行器严格匹配原始命令并创建 YAML 事务记录。
2. 按 `metadata-guide.md` 读取大纲、平台约束和标签候选库。
3. 生成五套完整方案至事务 staging 目录。
4. 记录正式目标基线摘要、staging 摘要和幂等键。
5. 已有正式文件时取得覆盖确认，并在 YAML 事务中精确绑定 `metadata/novel-metadata.md`；未确认则保持 staging，不提交。
6. 门禁与授权通过后，由事务执行器原子发布正式元数据。

## 相关规范

- [../metadata-guide.md](../metadata-guide.md)
- [../state-management.md](../state-management.md)
