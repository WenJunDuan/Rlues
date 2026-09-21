---
source_design_sha256: "884f530d3c22d8b3bd3eee271404be07529d63516a590e1b45bd43c524166305"
mode: "design"
---

# Review Packet — writer provenance 与仓库边界（rev 4）

## Decision

rev 2 新 P0（状态①吞回执）落点=**规则 0 叠加制**：回执存在即校验，与链检查独立，mixed writer 两者都过；三态只答缺链替代。八格矩阵入 design 正文成为编号权威。P1 七条全落：适配式恢复两段式回退、附录 A 补 M8/M11/M12/M13 与 R1 备份行格式、账本完整性作用域定死（lifecycle 仅 generator role、大小写归一、缺失/零行/单侧语义）、备份判据改 canonical 行+existsSync+ship 前不删时序、evidence 重算时序与 HEAD 正交明文、两豁免消费者入写集同判据、AC4 因果改述为 Start 端最小复现。P2：治理哈希 Non-goal+免责、AC8 附测量命令。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | M1-M7 负向 + 重算先红 + 唯一命中 + required()=false + G2 叠加先红 + 次序（回执坏优先于 M8） |
| AC2 | G1-G10 逐格（G9/G10 收紧面先红）；G5 先红；绿区不变；外层短路删除；role 归一；sprint_source schema 扩展+旧行混存 |
| AC3 | 伴随字段三分支（stale 先红）+ 豁免消费者同判据 + M13/R1 + no-change |
| AC4 | Start 端最小复现先红 + Stop 归属链 + sprint_source + 可观察降级 + CX/Pi 负向 + 主路径等价 |
| AC5 | exports + 两段式回退适配 + governance 续绿 + 四用例 + CC==Pi 字节 |
| AC6 | CC/CX 十格/containment/M1-M13 逐字 + Pi 同源点名清单（不含 validateShip） |
| AC7 | 自指双缓解 + gate-contracts 三端四件 |
| AC8 | 全套回归绿（基线 160 附测量命令） |

## 状态（rev 4）

三轮复核：rev1 两 P0 闭合、rev2 新 P0 闭合、rev3 新 P0（sprint_source × exact-key 互斥）与 P1×2/P2×3 本轮全落实。rev3 复核明示：闭合此三条后置信度 0.8，可直接派 impl 无需再开复核轮——据此进 impl（grok 施工）。

## 审查焦点（留档）

- 规则 0 叠加制的完备性：回执存在但损坏时 G2/G8 的判定次序；「存在即校验」对误放置回执文件（如模板复制残留）的过拦面。
- 八格表与三态文字的自洽（G6 消息沿用既有措辞是否与 M9 冲突）。
- 附录 A M1-M13 是否覆盖全部新 block 分支（无消息分支清点）；M8 长消息三端逐字可行性。
- 豁免消费者同判据后，合法仓外 sprint 的 spawn→impl→ship 全程走查（死锁复查）。
- grok 唯一实现置信度重估（上轮 0.5）。
