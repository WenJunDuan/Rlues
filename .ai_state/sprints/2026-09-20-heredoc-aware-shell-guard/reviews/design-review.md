---
schema_version: 1
mode: "design"
review_run_id: "eeed0a10-64e0-4313-935d-f4b706b81741"
reviewer_target: "a639b62532d78ac38"
packet_sha256: "967607c0052b632ec202f729e580d183aa9ecea9e06c9e99964c80af8bfe611d"
input_manifest_sha256: "bb56c6f1e79cbeaf39ee7a6147dc41e9d3299dc60f4d3350edce6738aad3f098"
native_output_ref: "reviews/_native/eeed0a10-64e0-4313-935d-f4b706b81741-result.json"
verdict: "REWORK"
---

## Native review output

---
schema_version: 1
mode: design
packet_sha256: "967607c0052b632ec202f729e580d183aa9ecea9e06c9e99964c80af8bfe611d"
review_run_id: "eeed0a10-64e0-4313-935d-f4b706b81741"
verdict: REWORK
finding_counts: {P0: 1, P1: 0, P2: 3}
dimensions: [spec, correctness, security, tests, overengineering]
---

P0-a' 识别上下文 fail-open **同因第二次**：rev 3 宣称的三条规则（注释感知/非正文行收集/单遍推进）在 design HOW 中零命中（grep 机械核对）——只把两个反例塞进 AC3，未立规则。枚举外新反例实测放行：行续反斜杠形态（heredoc 声明行以反斜杠续行、续行携带危险命令）bash 真执行续行命令，rev 3 的 bodyStart 物理行规则会把它掩进正文=放行（今日拦）。跨行引号伪声明同族（over-block 方向不计 P0）。要求三条规范化规则（含**逻辑行**语义）+ 默认不触发表述；**触发同因 P0 二次规则，停止自动返工，交还用户**（选项 a 规则收口后批准再审 / b 缩小方案面仅 quoted 单行声明掩码）。
P2-a 终止行尾随空白与 bash 不符（bash 实测不闭合），rev 3 取 over-block 可接受但须标注有意偏离；<<- 剥 tab/定界符名/CRLF 三条与 bash 一致实测通过。
P2-b 哨兵消费两条语义清晰但无 AC 绑定，要求入 AC4。
P2-c packet/design AC4 不双射（packet 有哨兵句 design 无）。写集零改动，无过度工程。

VERDICT: REWORK