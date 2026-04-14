---
description: 完整开发工作流，Path B/C，RIPER-10
---

# /dev - 完整开发

**触发词**: RIPER、完整开发、新功能、从0到1

**路径**: Path B (2-10文件) 或 Path C (>10文件)

## 工作流

```
R1感知 → I设计 → P锁定 → E执行 → R2闭环
```

## 执行步骤

### R1 - RESEARCH
```
1. memory.recall(project_path)
2. sou.search("<关键词>")
3. 仅读取直接相关文件
```

### I - INNOVATE
```
1. promptx.switch("AR")
2. sequential-thinking 深度推演
3. Linus审查清单检查
4. 多方案 → 寸止让用户选择
```

### P - PLAN
```
1. shrimp-task-manager 生成WBS
2. 寸止展示数据结构变更
3. 等待用户批准
4. 禁止未批准开始编码
```

### E - EXECUTE
```
1. promptx.switch("LD")
2. codex skill 执行任务
3. 自我修复(max 3) → 寸止请求人工
```

### R2 - REVIEW
```
1. 完整性校验
2. memory.add 固化决策
3. 寸止请求验收
4. 等待用户确认
```

## 寸止时机

| Path | 寸止点 |
|:---|:---|
| Path B | I确认方案 + R2验收 |
| Path C | 每个关键决策 + 每Phase完成 |
