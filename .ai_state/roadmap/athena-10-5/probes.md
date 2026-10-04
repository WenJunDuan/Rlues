# 10.5 探针（需本机 CLI；结论回填 `core/package/skills/pace/references/platform.md`）

| # | 探针 | 步骤 | 判定 |
|---|---|---|---|
| P1 | Codex code mode 是否触发 PreToolUse | `config.toml` 设 `features.code_mode.enabled = true`；临时把 hook 命令包一层 `tee -a /tmp/athena-hook.log`；让模型在 code mode 里 `tools.apply_patch` 写仓库文件、`tools.exec_command("git push")` | 日志出现对应 PreToolUse = 触发；否则 doctor 标红 + SessionStart 提示 |
| P2 | Codex `spawn_agent` 是否触发 PreToolUse（issue #49736） | 红区 sprint 中 spawn 一个不带 worktree 声明的写者 | 被 H4 拦 = 正常；未拦 = H4 在 CX 降级，RELEASE 明写 |
| P3 | Pi 1.0 codemode 内写入被拦 | 装 `dist/pi/<ver>/plugin`，`defaultTools: ["+codemode"]`，无 AC 的 sprint 中让脚本 `tools.write(...)` | 脚本内 promise 被拒且带 H1 reason |
| P4 | CC 插件壳可加载 | `claude --plugin-dir dist/claude-plugin/<ver>`；`claude plugin validate dist/claude-plugin/<ver>`；跑一个 Quick sprint 到 ship | validate 通过、H1/H2 生效 |
| P5 | CC 插件 `bin/` 对子 agent 与 hook 子进程可见 | 插件形态下让子 agent 执行 `athena status` | 可执行 = G-009 类问题由插件根治 |
| P6 | Codex 插件壳可装 | 本地 marketplace 指向 `dist/codex-plugin/<ver>`；装后 `/hooks` 受信；跑一个 Quick sprint | hook 握手可见、H1 生效 |
| P7 | Pi 硬 Stop | ship 阶段缺证据时让 agent 收尾 | 被续跑且带 H2 reason；同因 3 次后放行并记 G 行 |
| P8 | CC ≥2.1.288 下 hook 输出合法 | 安装器形态跑全流程，观察有无「hook 序列化失败 → 拦截」 | 无误拦 |
