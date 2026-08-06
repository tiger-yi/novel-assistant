# World Bible 核心工作流

系统严格依赖 `world/outline.md`，默认以一次 `创作第 N 章` 完成完整章节事务。`构思第 N 章` 只是可选的只读预演。

```mermaid
flowchart TD
    Start["创作第 N 章"] --> Preflight{"风格就绪且 World Bible 完整"}
    Preflight -->|"失败"| Stop["熔断并报告"]
    Preflight -->|"通过"| Plan["构思并自动采用推荐分支"]
    Plan --> Stage["写入 chapters/.staging/"]
    Stage --> Polish["纯文本润色"]
    Polish --> Count{"字数达标"}
    Count -->|"不足"| Expand["依据细纲补全"]
    Expand --> Polish
    Count -->|"达标"| Gates{"确定性与语义门禁"}
    Gates -->|"失败且未满3轮"| Repair["修正 staging 正文"]
    Repair --> Polish
    Gates -->|"失败3轮"| Stop
    Gates -->|"通过"| Prepare["生成 World Bible 变更集"]
    Prepare --> Conflict{"变更集有冲突"}
    Conflict -->|"是"| Stop
    Conflict -->|"否"| Publish["发布正式章节"]
    Publish --> Update["按固定顺序更新 World Bible"]
    Update --> Postflight{"事务后置校验"}
    Postflight -->|"失败"| Recover["记录恢复点，不声称完成"]
    Postflight -->|"通过"| Due{"归档到期"}
    Due -->|"否"| Finish["事务完成"]
    Due -->|"是且无歧义"| Archive["自动归档"]
    Due -->|"是但有歧义"| Pending["归档待处理，章节仍完成"]
    Archive --> Finish
    Pending --> Finish
```

## 阶段边界

- **准备阶段**只写 staging 正文与事务日志，生成审计证据和 World Bible 变更集，不修改正式章节或 World Bible。
- **提交阶段**发布正式章节并回写 World Bible，完成后执行一致性与幂等校验。
- **文本润色**只改变正文表达，不负责字数判定、世界观审计、状态回写或归档。
- **条件归档**由 `创作第 N 章` 一次性授权，仅在到期且范围无歧义时执行。

## 周期门禁

完整原创性审计在初始化大纲后、每 10 章、卷结束或主线/金手指/力量体系重大调整时执行。周期审计存在阻断项时，不得开始下一创作周期。

失败后不得自动覆盖或整文件回滚用户原有差异，必须报告事务 ID、最后成功步骤、已修改文件和恢复点。
