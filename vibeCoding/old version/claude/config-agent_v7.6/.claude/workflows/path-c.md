# Path C: System Development (系统开发)

> 适用：>10文件 / >300行 / 架构变更 / 从0到1

---

## 流程图

```
开始 → 创建 session.lock
     ↓
R1: 加载 skills/research.md（深度分析）
     ↓
I:  加载 skills/innovate.md（架构设计）
     ↓
    寸止 [DESIGN_FREEZE] ← 用户选择方案
     ↓
P:  加载 skills/plan.md（分阶段TODO）
     ↓
    寸止 [PLAN_READY] ← 用户确认计划
     ↓
E:  分阶段执行（每阶段寸止）
    ┌────────────────────────────┐
    │ Phase 1 → 寸止 [PHASE_DONE] │
    │ Phase 2 → 寸止 [PHASE_DONE] │
    │ Phase N → 寸止 [PHASE_DONE] │
    └────────────────────────────┘
     ↓
R2: 加载 skills/review.md（全量核对）
     ↓
    寸止 [TASK_DONE] ← 用户验收
     ↓
删除 session.lock → 结束
```

---

## 与 Path B 的区别

| 维度 | Path B | Path C |
|:---|:---|:---|
| 规模 | 2-10文件 | >10文件 |
| TODO | 单列表 | 分阶段 |
| 寸止 | 3次 | 3+N次（每阶段） |
| 设计深度 | 方案对比 | 完整架构文档 |

---

## 分阶段执行

### Phase 结构
```markdown
## Phase 1: 基础架构
- [ ] T-001: 项目初始化
- [ ] T-002: 数据库设计

## Phase 2: 核心功能
- [ ] T-003: 核心业务逻辑
- [ ] T-004: API接口

## Phase 3: 用户界面
- [ ] T-005: 页面组件
- [ ] T-006: 交互流程
```

### Phase 完成时
```
调用 cunzhi MCP

输出：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 [PHASE_DONE] Phase X 完成

## Phase X 核对
- [x] T-00X ✅
- [x] T-00Y ✅

## 整体进度
████████░░░░░░░░░░░░ 40% (2/5 Phases)

请选择：继续 / 暂停 / 问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 寸止点

| 点 | 时机 | 等待内容 |
|:---|:---|:---|
| [DESIGN_FREEZE] | 架构设计完 | 选择方案 |
| [PLAN_READY] | TODO生成完 | 确认计划 |
| [PHASE_DONE] | 每阶段完成 | 继续/暂停 |
| [TASK_DONE] | 全部完成 | 验收 |

---

## 检查清单

- [ ] session.lock 已创建
- [ ] 架构文档完整
- [ ] TODO 已分阶段
- [ ] 每个 Phase 都有寸止
- [ ] 全量核对完成
- [ ] 用户验收后 session.lock 已删除
