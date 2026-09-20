---
source_design_sha256: "c48cb9ea8be5a5acf11a459cc0e06fd4fb04da35ffe4bbe32ace1275d5f7737a"
mode: "design"
---

# Review Packet — contract parser diagnostics（rev 2）

## Decision

门禁的合同解析只认合同结构、认得下常用标题、失败时说清哪一层坏了。收窄 AC 提取到验收小节并排除成对反引号/围栏引用；标题接受五个别名（AC/验收 用严边界：行尾或冒号）；packet 零小节独立报错并列全标题；三端 packet 模板改用可识别标题；TDD 三类失败分层。仍全部 fail-closed。接管切片 3 字节断言移除；安装态同步单列到 ship 收口。

## 验收标准

| AC | Roadmap | 判据 |
|---|---|---|
| AC1 | Q12#8 | 别名严边界：`## AC`、`## 验收:` 识别；`## AC 覆盖表`、`## 验收 流程`、`## AC-1`、`## AC(草案)`、`## ACL 配置`、`## 验收流程说明` 不识别；本 design.md 实档 HOW 小标题不产生验收小节 |
| AC2 | Q12#8 | 无小节报错逐字列全五个标题；有小节但 0 条有效条目为另一条明确消息 |
| AC3 | Q12#7 | packet AC 集只来自验收小节结构；小节外合同外标识不产生 extra/missing；零小节独立报错列全标题；design 侧仍限定在验收小节 |
| AC4 | Q12#7 | 成对反引号 span 内 AC 标识不进覆盖集，落单反引号原样保留；围栏行不产生条目；design/packet/mapping 三消费点同规则 |
| AC5 | Q12#5 | TDD 空文件 vs 未解析出记录（含期望形状）、缺字段（record 序号+test_file+字段名）、时间序（三实际值）三层可区分；CC/CX 消息逐字同 |
| AC6 | 交叉项 | 字节断言测试删除；Pi `_review-binding` == CC 独立保留；roadmap 承接清单更正 |
| AC7 | 平行性 | AC1-AC5 同夹具驱动 CC/CX 判定与消息一致；Pi 四个同源解析函数与 CC 文本相等由测试机械断言 |
| AC8 | P0-1 | 三端 packet 模板含可识别验收小节标题；按模板新建 packet 过 `validateReviewPacket` 不因标题落 AC set mismatch |

## 审查焦点（rev 2 变化）

- P0-1 采 (b) 路线：改三端模板 + packet 零小节独立报错，不加 contract/acceptance mapping 别名（避免常见英文标题扩大识别面）。
- P1-1：AC/验收 别名边界收窄到行尾/冒号，与全名边界分离；负向集含本仓四处活体命中。
- P1-2：Pi 判据改为四函数文本相等的机械断言。
- P2 全收：行号更正（:915、:988-989）；AC3 措辞去矛盾；stripInlineCode 只置空成对 span；安装态同步时点声明在 ship 收口。

## 证据入口

- 现状缺陷行号：design WHY 节。基线 `4b0ba98`。
- 模板现文：三端 `templates/sprints/review-packet.md:13` 为 `## Contract`。
