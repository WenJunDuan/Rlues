# Roadmap: fullstack-delivery (全栈交付 skills 体系)

- 需求: requirements/fullstack-delivery-pack.md
- 建立: 2026-07-07; 用户已拍板切片 + 双 session 并行 (Rlues 跑 F1, quantum session 并行做约定包)

## 目标形态

**一个 pack, 八个 skill, 两层分离**:

```
Rlues vibeCoding/{claude,codex}/9.9.x/skills/fullstack-delivery/   ← skill 本体 (系统无关)
  ├─ scaffold-module-gen/    后端模块生成 (已有, F1 收编加强)
  ├─ scaffold-page-gen/      前端页面生成 (F2)
  ├─ db-schema-gen/          表设计文档 + DDL SQL 双文档 (F3)
  ├─ unit-test-gen/          单测 + debug loop + 测试报告 (F3)
  ├─ security-test/          静态清单 + 动态越权用例 (F4)
  ├─ playwright-e2e/         E2E (现有 playwright skill 无关化) (F4)
  ├─ project-data-reader/    运行期 MCP 读数 (已有, F5 完善, 依赖 quantum S3)
  └─ biz-delivery-loop/      编排器: 14 步 loop + checkpoint 门禁 (F5)

各项目仓库 docs/ai/convention-pack/                                ← 约定包 (系统相关)
  quantum-backend: BE 约定 (已有) + db/test 约定 (F3)
  quantum-front:   FE 约定 (F2, quantum session 并行推进中)
```

## 切片与依赖

| item | 交付 | 仓库 | 依赖 | 状态 |
|---|---|---|---|---|
| F1 | 框架设计: 家族边界 + 编排状态机 (PACE 特化) + checkpoint/回滚协议 + 报告 schema + token 统计 hook 设计 | Rlues | 无 | **进行中 (本 session)** |
| F2 | scaffold-page-gen skill; FE 约定包由 quantum session 并行产出后对接 | Rlues + quantum-front | F1 | pending |
| F3 | db-schema-gen + unit-test-gen skill + 报告模板; DB/测试约定 quantum 侧 | Rlues + quantum-backend | F1 | pending |
| F4 | security-test + playwright-e2e 无关化 + 环境编排约定接口 | Rlues + quantum | F2 | pending |
| F5 | biz-delivery-loop 编排 skill + checkpoint hook + token hook + project-data-reader 完善 | Rlues | F1-F4 (reader 另依赖 quantum S3) | pending |
| F6 | 端到端演练: 真实小业务全流程, 校准回滚协议 | quantum 三工程 | F5 | pending |

## 硬约束 (每个 item 都适用)

1. skill 本体禁写具体项目知识 — 全部框架知识经约定包注入 (S2 已实证的分层)。
2. 编排器复用 PACE 状态机/_index.md/delivery-gate/evidence-collector, 禁止平行状态机。
3. 安全语义默认启用: 沿用 quantum-backend decision "codegen-security-gates-default-on"
   (校验默认开 + 显式豁免 + grep 门禁) — 所有新 skill 的生成物同一标准。
4. checkpoint 门禁检查**证据**而非日志字符串 (S2 趟出的 delivery-gate 误报教训)。
5. 双端对称: 每个 skill CC (.claude/skills) 与 CX (.codex/skills) 同步交付。
