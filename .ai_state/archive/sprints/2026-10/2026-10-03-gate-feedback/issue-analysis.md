# Analysis

- G-006：pause 依赖陈旧 stage；review 以全区间聚合。按源变更提升到 impl，并从 log HEAD 边界排除暂停区间；旧无边界 log 仍包含所有提交，不猜归属。
- G-007：非文件定位实际已能解析，但合同只点名文件定位；明确证据定位并拒绝缺失 id。
- G-008：分类器无 docs kind；仅本仓 Markdown 固定字串单命令出口可证明。
- G-009：安装输出未检查 rc；hook PATH 不传回父环境，因此 agent 合同也明确自身 shell 前置。
- G-010：第一个 push 返回导致后续漏查；窄 heredoc 限制首行。检查全部 push 段、逐目标仓；闭合数据 heredoc 扩展到后续顶层命令，引用正文视为数据，未引用正文独立解析真实替换。后续 cd、条件可能仓集合、后台 cd 和嵌套 shell/替换均追踪实际目标。未知目录不回退 idle。协议无法安全拆执行，留账。
- G-011：--env 检查与 shell policy 分离；共用执行环境族并保留全部既有拒绝。NODE_ENV / *RC 豁免与安全单调冲突，留账。
