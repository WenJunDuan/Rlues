# Route Note — F4 security-test + playwright-e2e

- 感知: F3 fallback review PASS; roadmap 下一项 F4 是 security-test + playwright-e2e 无关化 + 环境编排约定接口。
- 候选: Feature vs Refactor。支持 Feature: 两个既有 skill 的同类增强; 反对 Refactor: 不改全局 hook/架构。
- 权衡: 爆炸半径中等 (CC/CX 双 skill + references/scripts/tests), 可逆, 非紧急, 需求清晰。
- 决策: Feature, confidence=0.82。
- 验收: 两个 skill 能消费 security/e2e/runtime-env contracts, CC/CX parity, 回归覆盖缺文件/缺 marker 失败。
