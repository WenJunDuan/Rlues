# RIPER-7 阶段编排 (v9.0.8)

## 阶段流: R₀ → R → D → P → E → T → V

### R₀ (预研/头脑风暴, Path B+ 独有)
触发: /vibe-dev 且 PACE≥B
工具: brainstorm skill + augment-context + cunzhi
输入: 用户需求
输出: .ai_state/design.md (方案草案)
检查点: cunzhi [DESIGN_DIRECTION]

### R (研究)
触发: R₀ 确认后 或 Path A 直接进入
工具: augment-context + deepwiki + WebSearch
输入: design.md 或 用户需求
输出: 更新 design.md (技术细节)
动作: 搜索现有代码, 查库文档, 确认技术可行性

### D (设计, Path B+ 独有)
触发: R 完成
工具: context7 + sequential-thinking (如可用)
输入: design.md
输出: design.md 终稿 (接口定义/数据结构/模块划分)
检查点: cunzhi [DESIGN_READY]

### P (规划, Path B+ 独有)
触发: D 确认后
工具: plan-first skill
输入: design.md
输出: .ai_state/plan.md (任务列表+依赖+预估+子代理分配)
检查点: cunzhi [PLAN_CONFIRMED]

### E (执行)
触发: P 确认后 或 Path A R 完成
工具: tdd skill + agent-teams (Path C+)
输入: plan.md (B+) 或 需求描述 (A)
过程:
  - Path A: 直接开发, 手动验证
  - Path B: tdd 分级, doing.md 看板跟踪
  - Path C/D: agent-teams 并行, worktree 隔离
输出: .ai_state/doing.md 更新, 代码变更

### T (测试/验证)
触发: E 完成
工具: verification + code-review skills, /review (官方)
输入: 代码变更
过程:
  - Path A: 功能验证 + lint
  - Path B: verification + code-review → verified.md
  - Path C/D: + e2e-testing + security-review
  - Codex: /review 原生代码审查
输出: .ai_state/verified.md
检查点: cunzhi [TESTS_PASSED] (C+: [SECURITY_PASSED])

### V (验收/交付)
触发: T 通过
工具: delivery-gate hook (自动), cunzhi
过程:
  1. delivery-gate 检查: plan 无未完成项 + 测试通过
  2. cunzhi [DELIVERY_CONFIRMED] 用户确认
  3. 写入 .ai_state/knowledge.md (经验沉淀)
  4. 归档 → .ai_state/archive.md
输出: 交付完成

## 九步工作流节点映射
需求创建(R₀) → 需求审查(R₀确认) → 方案设计(D) → 方案审查(D确认)
→ 环境搭建(P) → 开发实施(E) → 代码提交(E-commit) → 版本发布(V) → 完成归档(V-archive)
