- [P1] vibeCoding/athena/gate/cli/run.cjs:255 — 按 kind 提前过滤仍会丢弃同一命令的较新失败：已登记 VM 的 `athena run --covers AC1 -- ssh root@10.0.0.5 'npm test'` 先 PASS，删除 VM 登记后同 argv 返回 1，新记录成为 `kind=other`；同树执行 `--rebind` 实测仍 exit=0、零重跑、零失败。已入选执行身份必须关联所有较新 attempt，不能因分类改变复用旧 PASS。
VERDICT: REWORK
原 node 复现已修复，独立复跑 9 项重放测试通过；上述 SSH 分支仍需回归与修复。
AC1、AC4 覆盖；AC2、AC3 尚有上述缺口，无 EXTRA。
已核对当前树的 328 项全量及 2 项原生探针成功证据；构建检查通过。
U-001、真实平台事件与行为评测继续保留发布阻塞。
