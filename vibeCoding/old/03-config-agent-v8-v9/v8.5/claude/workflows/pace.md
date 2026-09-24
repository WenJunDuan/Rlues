# P.A.C.E. — 复杂度路由

> 收到需求后第一件事: 判断走哪条路径。路径决定每阶段的工具密度、检查点频率和并行策略。

## 决策树

```
收到需求
  │
  ├─ 改动 ≤ 20 行 + 单文件 + 无架构影响?
  │   └─ YES → Path A (Agile, 跳 R₀/R/D/P)
  │
  ├─ 涉及 1-3 文件 + 无新依赖 + 无 API 变更?
  │   └─ YES → Path B (Balanced, 快速 R₀→R→D)
  │
  ├─ 涉及 4+ 文件 / 新依赖 / API 变更 / 数据库迁移?
  │   └─ YES → Path C (Comprehensive, 完整流程 + 子代理)
  │
  └─ 跨模块 / 架构变更 / 需多 agent 协作?
      └─ Path D (Deep, Agent Teams + 完整流程)
```

## Path 配置

```yaml
Path_A:  # 30 分钟内
  phases: [E, T]
  cunzhi: 无
  tdd: 跳过
  test: npm test 通过即可
  parallel: 无

Path_B:  # 2-4 小时
  phases: [R₀, R, D, P, E, T, Rev]
  cunzhi: REQ_CONFIRMED, DESIGN_READY, PLAN_APPROVED, REVIEW_DONE
  tdd: 推荐 (核心逻辑)
  test: + lint + 类型检查
  parallel: explorer 调研

Path_C:  # 1-2 天
  phases: [R₀, R, D, P, E, T, Rev, A]
  cunzhi: 全部检查点
  tdd: 强制 (全覆盖)
  test: + 覆盖率 ≥ 80%, 无 TODO
  parallel: explorer 并行调研 → builder 并行实现 → validator 验证

Path_D:  # 1-3 周
  phases: [R₀, R, D, P, E, T, Rev, A]
  cunzhi: 全部检查点 + 阶段间确认
  tdd: 强制 + 集成测试
  test: + 性能基线 + 安全扫描
  parallel: Agent Teams, 按模块分 teammate
```

## 路径升级

执行中发现复杂度被低估 → 立即升级:
- 途中新增文件 > 3 个 → B 升 C
- 发现架构影响 → 任意升 C/D
- 需要并行开发 → 升 D

升级时 cunzhi `PATH_UPGRADE`, 不静默升级。

## 路径确定后

读 `workflows/riper-7.md` → 按当前 Path 从 R₀ 或 E 开始执行。
