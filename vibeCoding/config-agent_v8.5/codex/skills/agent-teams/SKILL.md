---
name: agent-teams
description: Path C/D 并行编排 — collab 并行调度子任务
context: main
---

# 并行协作 (collab)

## 调度规则

Path B: 串行搜索 → 实现 → 验证
Path C: collab 并行调研 → 实现 → 验证循环
Path D: collab 按模块并行, 每模块独立实现+测试

## 并行调度模板

```
collab 并行执行以下子任务:
1. [后端] 实现 {API}, 范围: src/api/
2. [前端] 实现 {组件}, 范围: src/components/
3. [测试] 编写 {测试}, 范围: tests/
要求: 子任务之间不修改对方文件
```

## 防冲突

按目录/模块划分写入边界, 子任务之间零文件重叠。
冲突时: 主代理仲裁合并。

## 串行回退

有强依赖链 (A→B→C) → 串行执行, 不强行并行。
同一文件多处修改 → 拆分不重叠区域或串行。
