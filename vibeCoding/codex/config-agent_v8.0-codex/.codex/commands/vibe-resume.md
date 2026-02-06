# vibe-resume

增强 `/resume`，从 .ai_state 恢复完整工作上下文。

## 执行流程

```
1. /resume                        # 调用官方
2. 读取 .ai_state/session.md      # 会话状态
3. 读取 .ai_state/doing.md        # 进行中任务
4. 读取 .ai_state/plan.md         # 当前方案
5. sou.search(进行中任务关键词)    # 加载相关代码
6. 汇报恢复状态 + 建议下一步
```

## 恢复优先级

1. doing.md 中有任务 → 继续执行
2. todo.md 中有任务 → 建议开始下一个
3. 全部完成 → 提示 vibe-archive 归档
