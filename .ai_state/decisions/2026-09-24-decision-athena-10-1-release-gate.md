---
doc: decision
created: "2026-09-24"
status: accepted
supersedes: ""
superseded_by: ""
---
# Athena 10.1 发布门修订：豁免行为评测

## 背景

- `roadmap/athena-10-1/design.md` §12「10.1 发布门」：fixture 三端全绿；行为评测对 9.9.9 不退化；Rlues 与 quantum-agent 迁移 dry-run 通过且 Rlues 实迁完成；安装/回滚演练一次；quantum-agent 在 10.1 上完成 ≥1 个真实 Feature sprint（major 条件）。
- S8 evals 已于 2026-09-24 由用户 drop（「后续在项目中跑评测再完善」），行为评测无基线、无对比表，该门项无法满足。

## 决定

用户 2026-09-24 裁定（方案 A）：10.1.0 直接定版，**豁免「行为评测对 9.9.9 不退化」**。其余门项不变：

| 门项 | 状态 |
|---|---|
| fixture 三端全绿 | 满足（156/156） |
| 行为评测不退化 | **豁免**（本决定） |
| Rlues 迁移 + 实迁 | 满足（406105a） |
| quantum-agent 迁移 dry-run | 满足（旧路径引用 blocker 16 → 0；已完成 v1 sprint 收尾并清空 current pointer） |
| 安装/回滚演练 | fixture 仿真满足（test_999_to_101_doctor_rollback）；真机 `install --dry-run` 已通过（write 234 / merge 3 / retire 148） |
| quantum 真实 Feature sprint | major 条件，10.1 为 minor，不适用；作为 10.1.x 发布后验证 |

这里的 major/minor 是 Athena 发布范围分类，不按 SemVer 首位数字推断：用户将本次 10.1.0 裁定为 minor；只有 roadmap 或发布 decision 显式标为 major，才触发「迁移后完成真实 Feature sprint」门项。该分类只解释原门项的适用范围，不构成第二项豁免。

## 后果

- 10.1.0 的「质量不退化」无量化证据；回退路径 = `athena rollback`（事务式，fixture 验证可逐字节回到 9.9.9）。
- 行为评测债记入 issues，下一个 minor（10.2）发布门恢复该项，不得再次豁免而不写 decision。
- quantum 在 10.1 上首个真实 sprint 中撞到的门禁问题按 10.1.x 热修处理。

## 补记（2026-09-24）：部署范围

用户裁定：10.1 **只部署 CC + CX，Pi 不部署**。S9 AC2 原写「安装到本机（cc,cx,pi）」，据此收窄；Pi dist 继续随构建产出与 fixture 覆盖，需要时 `athena install --platform pi` 补装。
