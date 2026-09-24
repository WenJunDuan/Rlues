# Path B: Planned Development (计划开发)

> 适用：2-10文件 / 30-300行 / 新功能 / 局部重构

---

## 流程图

```
开始 → 创建 session.lock
     ↓
R1: 加载 skills/research.md（感知理解）
     ↓
I:  加载 skills/innovate.md（方案设计）
     ↓
    寸止 [DESIGN_FREEZE] ← 用户选择方案
     ↓
P:  加载 skills/plan.md（生成TODO）
     ↓
    寸止 [PLAN_READY] ← 用户确认计划
     ↓
E:  加载 skills/execute.md（逐项执行）
     ↓
    更新 kanban（TODO→DOING→DONE）
     ↓
R2: 加载 skills/review.md（核对验收）
     ↓
    寸止 [TASK_DONE] ← 用户验收
     ↓
删除 session.lock → 结束
```

---

## 阶段详情

### R1 - RESEARCH
```
→ 加载 skills/research.md
→ 产出：需求理解、代码定位
```

### I - INNOVATE
```
→ 加载 skills/innovate.md
→ 产出：数据结构、方案对比
→ 寸止 [DESIGN_FREEZE]
```

### P - PLAN
```
→ 加载 skills/plan.md
→ 产出：TODO列表、kanban
→ 寸止 [PLAN_READY]
```

### E - EXECUTE
```
→ 加载 skills/execute.md
→ 逐项执行 TODO
→ 每项：TODO→DOING→DONE
```

### R2 - REVIEW
```
→ 加载 skills/review.md
→ 产出：核对报告、统计
→ 寸止 [TASK_DONE]
```

---

## 寸止点

| 点 | 时机 | 等待内容 |
|:---|:---|:---|
| [DESIGN_FREEZE] | 方案设计完 | 选择方案 |
| [PLAN_READY] | TODO生成完 | 确认/修改 |
| [TASK_DONE] | 全部完成 | 验收 |

**每个寸止都必须调用 cunzhi（降级 mcp-feedback）！**

---

## 检查清单

- [ ] session.lock 已创建
- [ ] 每个阶段加载了对应 skill
- [ ] 寸止点都调用了工具
- [ ] kanban 三态完整
- [ ] 用户验收后 session.lock 已删除
