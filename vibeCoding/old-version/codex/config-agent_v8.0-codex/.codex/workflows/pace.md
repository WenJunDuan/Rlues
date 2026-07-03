# P.A.C.E. v2.0 Workflow

## 路由流程

```
任务输入 → 复杂度评估
  │
  ├─ Path A (Quick Fix)
  │   effort=low → R1→E→R2 → cunzhi[TASK_DONE]
  │
  ├─ Path B (Planned Development)  
  │   effort=medium → R1→I→P→cunzhi[PLAN]→E→R2→cunzhi[DONE]
  │
  ├─ Path C (System Development)
  │   effort=high → 完整九步,每阶段cunzhi
  │
  └─ Path D (Agent Teams)
      effort=max → Lead分析→cunzhi[TEAM_PLAN]→并行执行→合并→cunzhi[TEAM_DONE]
```

## 所有路径共同要求

1. 写入 todo.md
2. 执行时移到 doing.md
3. 完成移到 done.md
4. 核对 todo vs done
5. cunzhi 确认
