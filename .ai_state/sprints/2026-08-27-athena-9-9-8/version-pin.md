---
sprint_slug: "2026-08-27-athena-9-9-8"
kind: version-pin
observed_at: "2026-08-27T11:20:00+08:00"
---

# Impl-entry version pin (AC13)

| # | 断言 | 实测 | 处置 |
|---|---|---|---|
| V1 | CC `/code-review` 后台 subagent，`/review` 为其别名 | `claude --version` → **2.1.231**（pin 写 ≥2.1.246）。2.1.221 起后台、2.1.223 别名已在本版本之前，**按 2.1.231 能力面落地异步 review**。2.1.233+ 的 todo 移除不作为本机唯一路径。 | 黄区：记录过期 pin，实现不依赖 2.1.246-only API |
| V2 | CX 仅执行 command/MCP hook | `codex --version` → **0.150.0**（记录曾是 0.145.0）。0.146+ 异步 hook/MCP 未用一手 schema 证实。Athena 9.9.8 仍只用 command hook；`/export` 不作唯一 `native_output_ref` 路径。 | 黄区：CX 0.146+ 特性非唯一实现 |
| V3 | 同事件多 hook 并发 | 9.9.6 现场 + 官方 hooks 文档未在本机用新 fixture 推翻 | 保持「同一事件最多一个同步 blocker」的 registry 收敛 |

`_index.cc_version` / `cx_version` 将更新为上述实测值。
