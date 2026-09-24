# Session log — S2 gate-core

- 2026-09-24：路由 System（athena-10-1 S2，用户「开 S2…全部做完，合并并提交」）；分支 athena-10.1 @e9abec6，单写者直接提交（偏差已记）。design AC1–AC9 + 已裁量偏差表 + 9.9.9 测试族处置表。
- 2026-09-24：实现 `vibeCoding/athena/gate/`（hook.cjs 单入口、core、lib×10、rules H1–H5 + advisory、platform cc/cx/pi、cli run）；CC settings.json / CX hooks.json 改指 `~/.athena/current/hook.cjs`；Pi 扩展进程内调用 vendored `plugin/core/gate`；build 新增 gate_root 与 `athena` dist；删除 CC/CX 全部旧 hooks 与 Pi cc-core；stages.yaml 改写为 H1–H5/A1–A10。
- 2026-09-24：fixture 迁入 evals（shell/hard/evidence/advisory/contracts/regressions），与冻结 9.9.9 实现做判决对拍（declared additions 除外）；test_build 改 declared-delta。
- 2026-09-24：独立 review 5 轮（REWORK×4 → CONCERNS），逐轮修复 + 回归 fixture，终态 89/89；athena999 231 OK。
- 2026-09-24：坑：git `update-index` 同时给 `--no-assume-unchanged --no-skip-worktree` 会静默丢一个（2.34/2.43 均复现），且 `--stdin` 下 `--no-skip-worktree` 无效 → 分开调用、argv 传路径。
- 2026-09-24：坑：VM shim 需把 tomli 装进 `$HOME/shim`（--target），否则 athena999 安装类测试在临时 HOME 下找不到 tomli（10 条假失败）。
