---
schema_version: 1
mode: "design"
review_run_id: "1831d96a-55f1-4560-97c9-1f16eb7d7024"
reviewer_target: "a38b598d5e78d750a"
packet_sha256: "435b75a17000ac196891cc45b95e0a1cf9e7881d33aea0abfda9e2f4f8000745"
input_manifest_sha256: "ead4b1ae49f4f245d09fee856f46e8501108d0bfd304c2e3296c29387974bd60"
native_output_ref: "reviews/_native/1831d96a-55f1-4560-97c9-1f16eb7d7024-result.json"
verdict: "REWORK"
---

## Native review output

---
schema_version: 1
mode: design
packet_sha256: "435b75a17000ac196891cc45b95e0a1cf9e7881d33aea0abfda9e2f4f8000745"
review_run_id: "1831d96a-55f1-4560-97c9-1f16eb7d7024"
verdict: REWORK
finding_counts: {P0: 1, P1: 3, P2: 4}
dimensions: [spec, correctness, security, tests, overengineering]
---

P0-1 谓词未规定「全部匹配」语义：5 个消费点全是 SECRET.search 首匹配，首个占位符即放行其下全部真密钥（实测混排 blob 复现）；C 侧行内首分隔符同病。修：finditer 全部匹配均占位才放行；C 逐分隔符取值；新增混排 AC。
P1-1 占位词子串匹配与 fail-closed 矛盾：sk-SAMPLE…/ghp_todo…/含 tbd 的真 key 被放行，随机 40 字符 key 误判率 0.144%。修：整值匹配或非字母数字边界+值体其余不呈高熵；TBD/TODO 只认整值。
P1-2 WHY 两例不成立：`"${API_KEY}"` 10 字符不中（需 ≥12）、`"<your-client-secret>"` 裸串需键名前缀。修 WHY 事实与 AC 夹具（≥12 字符+改前实测命中基线）。
P1-3 覆盖面缺口：SECRET 有 5 个消费点，306 validate_scenario 与 249 redacted 的行为变更零 AC。修：列全或 Non-goals 显式声明方向。
P2：①`<…>` 整值最弱，加值体 [A-Za-z0-9_.-] 且非高熵；②collect() 非静默（有 stderr+manifest 记录），WHY 措辞更正；③第 4 份同族正则 evidence-collector.py:32-42（CX 独有仅脱敏）Non-goals 点名；④Pi 悬空引用证实，归切片 9 正确。
核验为真：正则原文/五消费点行号/CC==CX 字节 24db5908/CC==Pi 22455eb4/c540b22 历史/写集穷尽性/不建豁免正当/双射无 EXTRA/反过度工程正当。阻断=P0-1+P1-1。

VERDICT: REWORK