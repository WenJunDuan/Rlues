# vibe-checkpoint

手动保存检查点。

## 执行流程

```
1. 读取所有 .ai_state/ 文件
2. 生成时间戳快照
3. 写入 .ai_state/archive.md (checkpoint section)
4. cunzhi [CHECKPOINT] 确认
```

## 输出

在 archive.md 追加：

```markdown
### Checkpoint: {{timestamp}}
- Plan: {{plan 摘要}}
- Done: {{已完成列表}}
- Doing: {{进行中列表}}
- Context: {{关键上下文}}
```
