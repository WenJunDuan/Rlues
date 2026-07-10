# Route Note — {slug}

> v9.9.1 路由决策摘要. 记录候选、证据、权衡、决策与置信度, 不记录私有思维链.

- **输入**: "{用户原话摘要, 一句}"
- **候选**: Feature (证据: 单模块新增端点) vs Refactor (证据: 触碰 auth 中间件, 反对: 中间件只读)
- **权衡**: 爆炸半径=单模块 · 可逆=高 · 紧急=低 · 不确定性=中
- **决策**: **Feature** · 置信度 0.7
- **假设**: auth 中间件只读不改
- **廉价退出**: 前 2 个 task 若触碰 >3 文件 → re-route

## Re-route (如发生, 追加)
- {date} Feature → Refactor · 触发: {机械/语义, 具体证据} · 补欠 stage: runtime-verify, polish, worktree
