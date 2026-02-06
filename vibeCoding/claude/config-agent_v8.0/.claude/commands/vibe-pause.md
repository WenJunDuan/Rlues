# vibe-pause

暂停当前工作流，保存状态。

## 执行流程

```
1. 当前 doing 任务状态写入 session.md
2. session.md 标记 paused: true
3. cunzhi [PAUSED] 确认
```

## 恢复

使用 `vibe-resume` 恢复。
