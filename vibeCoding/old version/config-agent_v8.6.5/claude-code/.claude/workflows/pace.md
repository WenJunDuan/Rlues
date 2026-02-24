# P.A.C.E. v5.0 — 复杂度路由

## 决策树

```
任务输入 → 类型判断
  │
  ├─ Bug/CI 失败 → Bug-Fix 快速通道 (CLAUDE.md)
  │
  ├─ Path A — ≤20行, 单文件, 无架构影响
  │   → E→V (CLAUDE.md 快速通道)
  │
  ├─ Path B — 中等, 多文件, 需设计
  │   → R₀→R→D→P→cunzhi→E→T→V→Rev→cunzhi
  │
  ├─ Path C — 大型, 多模块, 需架构
  │   → 完整九步, 每阶段 cunzhi, Task() 子代理并行 (worktree)
  │
  └─ Path D — 项目级, 跨模块, 多人天
      → Agent Teams 并行编排
```

## 偏移检测

执行中出现以下信号 → **STOP + 重新路由**:
- 改动量超预估 2x → 升级 Path
- 未预见的依赖 → 回 R
- 测试持续失败 → 回 D
- 用户说偏了 → 回 R₀b

## 评估维度

| 维度 | Path A | Path B | Path C | Path D |
|:---|:---|:---|:---|:---|
| 改动行数 | ≤20 | 21-200 | 201-1000 | >1000 |
| 影响文件 | 1 | 2-5 | 6-15 | >15 |
| 架构变更 | 无 | 小调整 | 新模块 | 新系统 |

## 工具矩阵

| 工具 | A | Bug | B | C | D |
|:---|:---|:---|:---|:---|:---|
| augment-context | ✓ | ✓ | ✓ | ✓ | ✓ |
| brainstorm skill | — | — | ✓ | ✓ | ✓ |
| context7 / deepwiki | — | 按需 | ✓ | ✓ | ✓ |
| cunzhi | — | — | ✓ | ✓(每阶段) | ✓ |
| explorer 子代理 | — | — | ✓ | ✓(并行) | ✓ |
| builder 子代理 | — | — | — | ✓(worktree) | ✓ |
| validator 子代理 | — | ✓ | ✓ | ✓ | ✓ |
| e2e-runner 子代理 | — | — | — | ✓ | ✓ |
| security-auditor | — | — | — | 按需 | ✓ |
| Agent Teams | — | — | — | — | ✓ |
| knowledge.md 更新 | 按需 | ✓ | ✓(Rev) | ✓(Rev) | ✓(Rev) |
