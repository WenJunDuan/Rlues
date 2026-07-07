# Route Note — F1: 编排框架设计

- 日期: 2026-07-07
- 感知: fullstack-delivery roadmap 首片。产出**设计文档** (框架级), 不产代码; 但设计质量决定 F2-F6 全部走向。
- 假设: 全部资产落 Rlues (框架仓库); quantum 只作引用案例。
- 四维: 规模大 (8 skill 边界 + 状态机 + 协议 ×3)、风险高 (设计错则 F5 编排器重写)、验收可写 (见下)、不确定性中 (PACE 集成点已有 S2 实证)。
- 决策: **path=System, 从 plan 起步** → design (critic ≥2 轮, plan_model 可切 fable) → 设计文档即交付, impl 仅限 skill 目录骨架与 schema 文件。
- 置信度: 0.82 (扣分项: token 统计 hook 依赖 CC transcript 结构, 需实测)
- 验收标准:
  1. design.md 覆盖 design-brief.md 全部 7 个设计点, 每点有决策 + 备选对比
  2. checkpoint 回滚协议表: 每个 CP 有机器可验标准 + 回滚目标 + loop 上限 + 人工升级条件
  3. 报告 schema (需求完成度/测试/token 消耗/遗留) 有字段级定义 + 样例
  4. 与 PACE 集成边界文档化: 谁写 _index.md、delivery-gate 扩展点、evidence 流
  5. critic ≥2 轮且 findings 全处置
