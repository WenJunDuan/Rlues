---
source_design_sha256: "0bf231d44718e3e383f31cffc1a8f0dff5c368886608ec718f55d8580b908e66"
mode: "design"
---

# Review Packet — writer provenance 与仓库边界

## Decision

外部写者从裸 skip flag 升级为 external-writer.json 严格回执（exact schema、ancestor 现场验、evidence 四轴绑定复用既有基元），R/S 下裸 flag 失效、绿区语义不变；containment 两检（ship 备份记录、跨 sprint stale flag）接入门禁；tracker 落账改取 worktree 自身 `_index`（spawn 时刻快照=事件真 sprint），redirect 失败与事件丢失显式可观察；gate 导出两 helper、_review-binding 复写消除（切片 3 承接闭合）。CX/Pi 只同构其实际拥有的机制。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 回执全 schema 校验 + 负向矩阵；R/S 裸 flag block（先红）；绿区不变 |
| AC2 | flag=true 无备份记录 ship block（先红）；stale flag 拦下一 sprint impl-entry（先红）；本 sprint ship 期合法 |
| AC3 | worktree Start 取自身 `_index` slug（指针错位夹具先红）；redirect 失败带标记；丢弃有痕迹；CX/Pi 负向断言 |
| AC4 | exports 两名 + 复写删除改 require + governance 续绿 + `.git` 边界直接用例 + CC==Pi 字节 |
| AC5 | CC/CX 同夹具三态与 containment 判定一致 |
| AC6 | roadmap 承接清单更正（切片 3 遗留②完成） |
| AC7 | 全套回归绿 |

## 审查焦点

- 三态分派的完备性：assignments 有 generator 行 / 有回执 / 皆无 × path 的组合矩阵有无漏格（如 generator 行存在但 lifecycle 不完整时是否还能靠回执兜底——应否？）；「两者并存分别校验」对混合施工的语义。
- 回执字段的可伪造面：全部字段由主 agent 手写，哪些校验是真机械（ancestor、evidence 命中、文件实存）哪些是纸面（executor 名）——与「不宣称密码学证明」声明的一致性。
- tracker 改动对非 worktree 主路径的等价性；worktree `_index` 缺失时回退链。
- containment 备份记录的机械判据（正则）会否过松/过紧。
- 施工将由 grok 外部执行（用户指定），本切片 ship 时以自产 external-writer.json 自校验——该自指路径的循环依赖风险（新校验代码由它要校验的流程交付）。
