---
name: quantum-codegen
description: >-
  全栈代码快速生成 (quantum 适配层). 按 mode 生成: 前端页面/组件 (page) · 后端模块脚手架 (module) ·
  数据库表结构与 DDL (db) · 后端单元测试 (unit) · 安全测试 (security) · 端到端 E2E 测试 (e2e).
  当用户说"生成页面/建模块/建表/写单测/安全测试/E2E", 或 biz-delivery-loop 编排到对应 stage 时触发.
  系统无关: 只读 Convention Pack + runtime-env, 证据写 PACE runtime-verify.
---

# quantum-codegen — 全栈代码快速生成

> 6 种生成模式合一 (7→2 合并; 前身 scaffold-page-gen / scaffold-module-gen / db-schema-gen / unit-test-gen / security-test / playwright-e2e).
> 热路径只做 mode 选择 + 共同契约; 各栈详细步骤/规范/适配器下沉 `references/`, 按 mode Read (渐进披露).

## 共同契约 (一次声明, 不再逐 mode 重复)

- **系统无关**: 生成逻辑不写死技术栈; 具体栈从 `references/*-convention-pack.md` + `quantum-*-adapter.md` 读取.
- **只读约定**: 先读对应 Convention Pack + runtime-env, 不臆造路径/命名.
- **证据**: 产物 + 校验脚本输出写进 PACE runtime-verify (delivery-gate 只认落盘证据, 不认对话).
- **自修复 loop**: 跑 `scripts/check_*.py` → 读失败 → 修 → 重跑到过.

## mode 选择表

| mode | 生成什么 | 详细步骤 | 规范 / 适配器 | 校验脚本 |
|---|---|---|---|---|
| **page** | 前端页面/组件 | `references/page-playbook.md` | frontend-convention-pack.md + quantum-front-adapter.md | scripts/check_frontend_pack.py |
| **module** | 后端模块脚手架 | `references/module-playbook.md` | (随 db/unit 栈) | scripts/check_backend_pack.py |
| **db** | DB 表结构 + DDL | `references/db-playbook.md` | backend-db-convention-pack.md + quantum-backend-db-adapter.md | scripts/check_backend_pack.py |
| **unit** | 后端单元测试 | `references/unit-playbook.md` | backend-test-convention-pack.md + quantum-backend-test-adapter.md | scripts/check_backend_pack.py |
| **security** | 安全测试 | `references/security-playbook.md` | security-test-contract.md + quantum-security-adapter.md | scripts/check_security_e2e_pack.py |
| **e2e** | 端到端测试 | `references/e2e-playbook.md` | e2e-convention-pack.md + quantum-e2e-adapter.md | scripts/check_security_e2e_pack.py |

## 用法

1. 定 mode (上表).
2. Read 该 mode 的 playbook + 规范/适配器.
3. 生成代码到适配器约定的路径.
4. 跑对应 `check_*.py`, 输出写 runtime-verify.
5. 失败 → 自修复 → 重跑.

## 边界 (不并入本 skill)

- 通用依赖检查 → `deps-check` skill.
- 浏览器驱动实跑 (e2e mode 借用) → `playwright` skill.
- 运行期数据/能力读取 (读, 非生成) → `quantum-data` skill.
