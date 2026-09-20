---
schema_version: 1
mode: "design"
review_run_id: "9929ee26-f80f-47e4-bff2-e8683b53ab71"
reviewer_target: "ac68650c220cd5d48"
packet_sha256: "00fcdf05fde9e3e0a57ab9d5f880d8a95298939a7525ed79011fb029d7013d9d"
input_manifest_sha256: "64982c6fb1518c6d5f38d81e4e903033561f270d53cbdda676399b93510231c4"
native_output_ref: "reviews/_native/9929ee26-f80f-47e4-bff2-e8683b53ab71-result.json"
verdict: "REWORK"
---

## Native review output

---
schema_version: 1
mode: design
packet_sha256: "00fcdf05fde9e3e0a57ab9d5f880d8a95298939a7525ed79011fb029d7013d9d"
review_run_id: "9929ee26-f80f-47e4-bff2-e8683b53ab71"
verdict: REWORK
finding_counts: {P0: 2, P1: 1, P2: 3}
dimensions: [spec, correctness, security, tests, overengineering]
---

核心断言一半成立：8 个对抗首行实测安全（$V 展开/重定向/声明后参数/管道/双声明拒/分号多命令/续行次行声明/同行命令不掩）。失效点唯一：第 3 条只约束字符集，不证明 << 处于重定向位置。

P0-1（同因第四次）算术上下文逃逸：(( 1 << 'a' )) / $[ 1 << 'a' ] / if (( … )) / 数组下标 [1<<'i'] 四形态满足窄形全部条件、定界符名取引号内字面、后文存在同名物理行 → 掩真实执行行。排除性反证：let/declare -i 的 << 仍是重定向，掩码正确=有界集。修法有界：第 3 条黑名单加 ( 与 [（保守版），五反例入 AC3 先红。
P0-2 unquoted 豁免非单调实测证伪：正文英文撇号（don't）留在主扫描流 → findSubstitutions 进入永不闭合单引号态 → 今日 BLOCK 的 $(rm -rf /) 变 ALLOW。底层奇数引号遮蔽为既存缺陷，但本切片把今日拦的输入变放行=计 fail-open。修法有界：正文以独立字符串从干净词法态单独扫替换再并入，严格单调。
P1-1 窄形正向用例三缺口（<<- 只剥 tab 不剥空格/终止行尾随空格不闭合/首行同行内容永不掩）需 AC 钉。
P2-1 定界符 token 终点写死（名=引号内字面，右引号后残留破坏窄形）。P2-2 悬空承诺清点补 roadmap.md:73 与 items.yaml:60。P2-3 通过项：$VAR 许可正确、裸定界符歧义全落 over-block、双射 7/7、等价矩阵覆盖前四轮档案完整。

合同处置：与前三次 P0 同根因（guard 对 shell 词法自信地错、错处即掩码吞真实执行），同因第四次，不得自动进 rev 6，交还用户。决策信息：本轮修复面有界且不回全文法路线；建议 rev 6 把安全论证改为正向枚举（窄形成立 ⇒ << 必在重定向位置）。证据脚本 /tmp/hdadv/ 可复跑。

VERDICT: REWORK