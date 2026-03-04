# VibeCoding Kernel v9.0.5 — Codex CLI

## 铁律 (违反即失败)
1. **先搜后写**: augment-context-engine 搜现有实现 → 不可用时 grep -r
2. **先规后码**: Path B+ 任务必须先 plan.md → cunzhi 确认后才能写代码
3. **不确定就问**: 歧义/架构决策 → cunzhi 向用户确认, 不猜
4. **不破坏已有**: 改代码前读测试, 改后跑测试, 红了就修
5. **只改需要改的**: 不重构范围外代码, 不加未要求的功能
6. **避免过度工程**: 最简方案, YAGNI 优先
7. **commit 粒度**: 每个逻辑变更独立 commit, conventional commits

## 工作流
1. 评估复杂度 → P.A.C.E. 路由 (读 .codex/workflows/pace.md)
2. 按路径执行 RIPER-7 阶段 (读 .codex/workflows/riper-7.md)
3. 按需加载 skills (读 .codex/skills/{name}/SKILL.md)

## 状态持久化
.ai_state/ 目录: session → design → plan → doing → verified → review → archive
模板位于 .codex/templates/ai-state/

## MCP 降级
augment-context 不可用→grep | cunzhi 不可用→对话确认 | deepwiki 不可用→/search

## Codex 专属能力
- /review: 原生代码审查 (T 阶段集成)
- /plan: 原生规划模式 (P 阶段集成)
- collab + parallel: 多代理并行 (Path C+)
- sub-agent fork: 从线程分叉子代理
- spawn_agents_on_csv: 批量多代理分派
- voice (spacebar): 语音输入 (实验性, features.voice_transcription=true)
- /model: GPT-5.3-Codex (默认) / GPT-5.3-Codex-Spark (快速)

## 并行工作规范 (Path C/D)
1. 读 plan.md → 识别无依赖任务组
2. 为每组 fork 子代理
3. 无依赖任务并行, 有依赖串行
4. 同文件不并行修改
5. 完成后合并 + /review 审查
