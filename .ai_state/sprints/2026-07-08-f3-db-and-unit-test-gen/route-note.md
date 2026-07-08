# Route Note — F3 db-schema-gen + unit-test-gen

- 感知: F2 review PASS; roadmap 下一项 F3 是 db-schema-gen + unit-test-gen 对接 quantum-backend Convention Pack。
- 候选: Feature vs Refactor。支持 Feature: 两个已存在 skill 的同类增强, 不改全局 hook/架构; 支持 Refactor 的证据不足。
- 权衡: 爆炸半径中等 (CC/CX 双 skill + references/scripts/tests), 可逆, 非紧急, 需求清晰。
- 决策: Feature, confidence=0.84。
- 验收: 两个 skill 能定位/校验 quantum-backend DB/Test Convention Pack, CC/CX 保持 parity, 回归覆盖缺文件/缺 marker 失败。
