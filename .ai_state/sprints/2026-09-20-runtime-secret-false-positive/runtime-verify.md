---
sprint_slug: "2026-09-20-runtime-secret-false-positive"
verified_at: "2026-09-20"
result: PASS
---

# Runtime Verify — runtime secret 假阳性

实现合入 main（ff，`86b39a8` 顶端）后以真实 CLI 进程实跑（fixture /tmp/rv7-fix，git 仓 + 真实 tar bundle）。

## 测试场景

| # | 场景 | 结果 |
|---|---|---|
| S1 | contract 含占位符示例 `api_key = "YOUR_API_KEY_HERE"` → run | status=passed, blocks_delivery=false（改前必 block） |
| S2 | contract 含真密钥（ghp_ 34 字符） → run | status=input_invalid, blocks_delivery=true |
| S5 | 混排 contract（占位 + 真密钥同文件） → run | input_invalid（AC7 端到端） |
| S3a | required 输入 `token = "${OPENAI_API_KEY}"` → snapshot | snapshotted, excluded=[] |
| S3b | required 输入真密钥 → snapshot | `runtime input rejected: required input missing or excluded` |
| S4 | environment()：`recipe: uses token: placeholder` 不抛；`recipe: token=ghp_…` 抛 credential syntax | 双向达 |

佐证：主仓全套 discover **137/137 全绿**（generator worktree 所见 8 条"既有失败"在主仓不复现，与切片 4 复核 P2-2 结论一致，属 worktree 环境探针）；CC==CX runtime-run 与 CC==Pi _input-binding 字节相等主 agent 复核。S4 为发行文件进程级模块加载（environment 无独立 CLI），如实注明。
