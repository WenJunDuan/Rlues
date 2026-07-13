# Route Note — Athena 9.9.2 architecture convergence

- **候选 A**: Quick/patch 清账，仅修版本漂移、插件配置与 pace 去重。
- **候选 B**: System 整体升级，完整落地四原语、spec-gate、两层记忆、双端安装迁移与验证闭环。
- **证据**: 用户明确指定版本仍命名为 `9.9.2`，并明确要求全部结构项落地；改动横跨 CC/CX 提示词、skills、hooks、模板、setup/migrate、harness 与 `.ai_state`。
- **权衡**: 爆炸半径高、门禁行为改变、必须双端兼容；需求已经足够明确，可直接写出验收标准。
- **决策**: `System`，沿用 `9.9.2` 版本号；本 sprint 先完成正式 review/实现合同，再交 Fable5 实现。
- **置信度**: `0.99`。
- **廉价退出点**: 仅当官方运行时契约证明某项不可实现时，将该项记录为明确 blocker；不得静默降级或回退为 patch 范围。

