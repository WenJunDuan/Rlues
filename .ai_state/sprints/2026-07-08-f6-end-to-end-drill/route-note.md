# Route Note — F6 end-to-end drill

- 感知: F1-F5 completed; roadmap 最后一项 F6 是 quantum 三工程真实小业务端到端演练。
- 候选: Feature vs System。支持 Feature: 演练一个小业务切片; 支持 System: 跨三工程真实运行。最低按 Feature 执行, 发现需改多仓核心则升 System。
- 权衡: 爆炸半径中高, 可逆性取决于演练是否写业务代码, 非紧急, 真实环境输入存在不确定性。
- 决策: Feature with upgrade guard, confidence=0.80。
- 验收: 审计 FE/BE/AI 工程运行条件, 用 F5 loop 合同跑一个可复验切片; 缺 runtime-env/MCP/test accounts 时落为明确 blocker。
