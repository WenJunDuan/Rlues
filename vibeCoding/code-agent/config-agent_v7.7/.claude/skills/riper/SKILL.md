# RIPER Skill

## 概述
RIPER 是 VibeCoding 的核心开发流程框架，将软件开发分解为五个有序阶段。

## 名称含义
- **R** - Research (感知理解)
- **I** - Innovate (方案设计)
- **P** - Plan (任务规划)
- **E** - Execute (执行开发)
- **R** - Review (验证闭环)

## 阶段流程
```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Research│ ──▶ │Innovate │ ──▶ │  Plan   │ ──▶ │ Execute │ ──▶ │ Review  │
│  (R1)   │     │   (I)   │     │   (P)   │     │   (E)   │     │  (R2)   │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
   感知            设计            规划            执行            验证
```

## 路径适配

| 路径 | 条件 | 阶段 |
|:---|:---|:---|
| Path A | 单文件 & <30行 | R → P → E → R |
| Path B | 2-10 文件 | R → I → P → E → R |
| Path C | >10 文件或跨模块 | R → I → P → [E → R]×n |

## 子技能文件

| 文件 | 阶段 | 说明 |
|:---|:---|:---|
| research.md | R1 | 需求分析、代码探索、依赖识别 |
| innovate.md | I | 方案设计、技术决策、风险评估 |
| plan.md | P | 任务拆解、排序、TODO生成 |
| execute.md | E | 代码实现、重构、状态更新 |
| review.md | R2 | 验证、测试、经验沉淀 |

## 加载策略

### 按需加载
```yaml
进入 Research 阶段 → 加载 skills/riper/research.md
进入 Innovate 阶段 → 加载 skills/riper/innovate.md
进入 Plan 阶段 → 加载 skills/riper/plan.md
进入 Execute 阶段 → 加载 skills/riper/execute.md
进入 Review 阶段 → 加载 skills/riper/review.md
```

### Path A 精简加载
```yaml
# Path A 跳过 Innovate
加载顺序: research.md → plan.md → execute.md → review.md
```

## MCP 工具集成

| 阶段 | 推荐工具 | 用途 |
|:---|:---|:---|
| Research | sou, context7, memory | 代码搜索、需求分析、历史查询 |
| Innovate | sequential-thinking, memory | 深度推理、决策存储 |
| Plan | mcp-shrimp-task-manager, memory | 任务管理、计划记录 |
| Execute | codex | 代码生成 |
| Review | playwright, memory | 测试执行、经验沉淀 |

## 寸止点

| 阶段后 | Token | 说明 |
|:---|:---|:---|
| Plan | `[PLAN_READY]` | 等待用户确认计划 |
| Innovate (Path C) | `[DESIGN_FREEZE]` | 等待用户确认设计 |
| Review (Path C) | `[PHASE_DONE]` | 等待用户确认阶段 |
| Review (最终) | `[TASK_DONE]` | 等待用户验收 |

## 使用示例

### 触发 RIPER
```bash
/vibe-code "添加用户登录功能"
# 自动评估复杂度 → 选择路径 → 执行 RIPER
```

### 单独使用某阶段
```bash
/vibe-plan "重构认证模块"    # 只执行 R → I → P
/vibe-design "设计插件系统"  # 只执行 R → I
```

## 质量保证

### 阶段转换检查
```yaml
R → I: 需求是否理解清楚
I → P: 设计是否合理
P → E: 计划是否完整
E → R: 代码是否完成
R → 完成: 验证是否通过
```

### 回退机制
```yaml
若验证失败:
  1. 记录问题
  2. 回退到 Execute
  3. 修复后重新 Review
```
