---
schema_version: 1
mode: "design"
review_run_id: "fb828b78-f3f1-44d1-a350-fe1c2e40b5dd"
reviewer_target: "ac121527cfbfb2310"
packet_sha256: "8f2df27cfae5b4b0dfd56db6a181f2a528a0b2efa279edcfeae8a60a255a9542"
input_manifest_sha256: "c49966797ff8dee1aac3ee864e44eec6038e3785be46fa3cc803398b63e76c7b"
native_output_ref: "reviews/_native/fb828b78-f3f1-44d1-a350-fe1c2e40b5dd-result.json"
verdict: "REWORK"
---

## Native review output

---
schema_version: 1
mode: design
packet_sha256: "8f2df27cfae5b4b0dfd56db6a181f2a528a0b2efa279edcfeae8a60a255a9542"
review_run_id: "fb828b78-f3f1-44d1-a350-fe1c2e40b5dd"
verdict: REWORK
finding_counts: {P0: 1, P1: 1, P2: 2}
dimensions: [spec, correctness, security, tests, overengineering]
---

上轮全 CLOSED（行续/注释行/内嵌/跨行引号四反例按 R1-R3 推演均拦；P2 三条落实；双射 7/7；写集零变化）。

P0-1 逻辑行终点只按行尾反斜杠定义 → bodyStart 过早 → 掩码吞真实执行行（**识别上下文类同因第三次**）。两个新反例 bash 实测真执行、今日拦、rev 4 推演放行：A=双引号内行尾反斜杠实为续行（R1 误判不合并）；G=未闭合引号跨物理行延长命令行（R1 无此形态）。根因：R2 默认不触发只覆盖「声明是否成立」，不覆盖「掩码区间端点」。要求：R1 改词法完整性定义（单引号内反斜杠不续行、双引号与裸均续行、任一引号未闭合则逻辑行继续）+ 新增 R4 区间方向性兜底（任一端点无法证明⇒整条跳过掩码=今日行为）+ A/G 入 AC3 先红。按合同不得自动进 rev 5，交还用户。

P1-1 终止行匹配层未定义：bash 对 unquoted 正文做续行合并再比对、quoted 不合并；按逻辑行统一合并会在 quoted 侧吞执行行=fail-open。要求写死「终止行按物理行匹配，unquoted 侧偏离标注 over-block」+ AC3 一例。
P2-1 引号/转义定界符的终止行比较基准未写（去引号去转义后的字面），否则永不闭合触发新误拦；AC3 负向各一例。
P2-2 注释止于物理行行尾、不参与续行合并，一句钉死防两端实现分叉。

证据：反例脚本 /tmp/{t1,b,b2,c,e,g}.sh 可复现；C 形态（替换内声明）按 R1-R3 推演正确无残余。

VERDICT: REWORK