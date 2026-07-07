# F1 Design Brief — 设计输入 (quantum session 移交, 2026-07-07)

> 本文件是设计**输入**, 不是设计本身。F1 执行者 (Rlues session) 按此出 design.md, 每点给决策 + ≥1 备选对比。

## 7 个必答设计点

### 1. 编排状态机: 14 步 → PACE stage 映射

用户 14 步 loop (原文见 requirements/fullstack-delivery-pack.md) 映射建议 (待设计确认/修正):

| 用户步骤 | PACE 承载 | 新增/复用 |
|---|---|---|
| 接受需求清单 | requirements/ 落档 (athena-requirements) | 复用 |
| 拆分 Sprint | roadmap stage | 复用 |
| ✚API 契约冻结 (洞①) | design stage 子产物 contracts/openapi | **新增子步** |
| 效果图 (HTML mockup+截图, 洞②) | design stage 子产物 | 新增子步 |
| CP① 效果图确认 | 人工 checkpoint (AskUserQuestion / 停机确认) | 新增 |
| 前端 demo (mock 从契约生成) + 本地运行 | impl stage (scaffold-page-gen) + runtime-verify | 复用+扩展 |
| CP② demo 可运行 | delivery-gate 扩展: dev server 启动探活 | 新增门禁 |
| DB 双文档 (表设计 md ∥ DDL sql) | design/impl (db-schema-gen) | 新增 skill |
| CP③ schema 评审 | 人工 checkpoint | 新增 |
| 后端代码 | impl (scaffold-module-gen) | 复用 |
| CP④ 编译+G门禁 | delivery-gate (已有 G1-G4 先例) | 复用 |
| 单测+debug+测试报告 | runtime-verify (unit-test-gen) | 新增 skill |
| 前后端对接 (契约 diff) | integration 子步: mock→真实接口, openapi diff | 新增 |
| review 三件套 | review stage | 复用 |
| playwright + 安全测试 | runtime-verify 扩展 (需环境编排, 洞③) | 新增 skill×2 |
| 需求核对 | spec-compliance (对 requirements 原始清单) | 复用 |
| 交付报告 | ship 前产物 (schema 见设计点 4) | 新增 |
| CP⑤ 人工确认 | 人工 checkpoint | 新增 |
| 跟随指令发布 | ship stage | 复用 |

**硬约束**: 不建平行状态机 — 状态唯一权威是 _index.md, 编排器只经既有 hook/stage 机制驱动。

### 2. checkpoint 分类与回滚协议

- 两类 CP: 机器门禁 (delivery-gate 家族, 证据可验) vs 人工确认 (CP①③⑤, 停机等用户)。
- 回滚目标表: 每 CP 定义 fail → 回到哪一步 (非回起点), 例: CP④ 编译失败 → 后端 impl; 对接契约 diff 失败 → 判定 mock 侧改或 BE 侧改。
- loop 上限: 同一 CP 连续 N 次 fail (建议 N=3) → 停机人工, 记 issue 档案。
- **门禁检查证据而非日志字符串** — S2 趟出的教训 (delivery-gate 靠 grep "generator" 误报, 见 quantum-backend sprints/2026-07-06-s2-scaffold-loop-verify/subagent-log.md 补录案例)。

### 3. skills 家族边界 (8 个)

每个 skill 一句话职责 + 输入 (约定包 section) + 输出 (产物+证据) + 禁区。特别:
- scaffold-page-gen: 消费 quantum-front 约定包 (quantum session 并行产出中, 结构对齐 shadcn-admin:
  feature 模块 = index.tsx/api.ts/model.ts/search-schema.ts/*-access.ts, TanStack Router 动态路由)
- db-schema-gen: **两个分离文档** — 表设计.md (语义/字段/索引/权限归属) 与 DDL.sql (可执行), 互相引用
- unit-test-gen: 内嵌 debug loop (跑→读失败→修→重跑), 报告按 schema 输出
- security-test: 圈范围 — 静态 (security-checklist grep + 依赖审计) + 动态 (认证/越权/数据域用例), 明确不做全自动渗透
- biz-delivery-loop: 只编排不实现, 每步产物路径与证据由被调 skill 声明

### 4. 交付报告 schema

字段级定义 + 样例: 需求完成度 (逐条 requirement→状态→证据)、FE/BE 测试报告 (用例数/通过率/覆盖关键路径)、
**模型与 token 消耗** (按 stage×model 分桶)、遗留问题、人工确认清单。格式 YAML frontmatter + md 正文 (机器可解析)。

### 5. token 统计 hook

CC 侧 usage 在 transcript/subagent 返回 (`<usage>subagent_tokens</usage>` 已可见); CX 侧待查。
设计: 新 hook 或扩展 evidence-collector, 按 sprint 累计, 写 sprints/{slug}/token-usage.yaml。需实测 CC transcript 结构。

### 6. 环境编排约定接口 (洞③)

约定包新 section "runtime-env": 声明起 FE/BE/DB 的命令、端口、探活 URL、teardown。skill 只读声明执行, 不猜。
quantum 参考: BE=mvn spring-boot:run (dev profile, cache.mode=local), FE=bun dev (vite), DB=容器或本地 PG。

### 7. 双端对称与分发

CC (.claude/skills) / CX (.codex/skills) 同步; 沿用 install-to-rlues.sh 模式做 pack 级安装脚本。
已知 CC/CX hook 差异: CX read_field 正则无 slice(1,-1) 病 (366ee6b 案例), 设计时列差异矩阵。

## 已知缺陷输入 (设计必须消化)

1. SubagentStop hook: worktree 内运行日志写进 .ai_state 副本随清理丢失 + subagent_name 恒 unknown
   (修复任务已另行进行中 task_3103e538, F1 设计假定其修复完成, 但 checkpoint 门禁仍按"验证据不验日志"设计)。
2. delivery-gate 机械 grep 的四次误报/卡点案例 (quantum-backend S2 sprint 全记录) — 门禁设计的反面教材。

## 参考材料 (跨仓库)

- quantum-backend: docs/ai-sprint-design.md (三平面/两契约/S 切片), docs/ai/convention-pack/ (BE 约定包全套),
  .ai_state/compound/2026-07-06-decision-codegen-security-gates-default-on.md,
  .ai_state/sprints/2026-07-06-s2-scaffold-loop-verify/runtime-verify.md (S2 端到端实证)
- Rlues: vibeCoding/claude/9.9.0/.claude/skills/{scaffold-module-gen,project-data-reader,pace,athena-runtime-verify}
