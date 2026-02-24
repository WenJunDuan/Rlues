智能开发入口 — 接收需求, 自动路由:
1. 接收用户输入 → 复述需求理解
2. 读 `workflows/pace.md` → 判定 Path (A/B/C/D)
3. Path A → 直接执行 (铁律中的快速通道)
4. Path B+ → 进入 `workflows/riper-7.md` 完整流程
5. 全程维护 `.ai_state/` 状态文件
