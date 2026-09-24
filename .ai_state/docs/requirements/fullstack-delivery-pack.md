# Requirement: fullstack-delivery-pack (全栈交付 skills 体系)

- 提出: 2026-07-07, Mi_Manchi (原话记录 + Claude 梳理)
- 状态: accepted, roadmap=fullstack-delivery
- 消费方: quantum 三工程 (front/backend/cowork-ai) 为首个试验场; 设计目标是脚手架无关, 任何项目换约定包即用

## 原始诉求 (用户原话要点)

1. 后端生成 skills 加强; 读前端工程同步生成前端 skills; 加数据库创建、单元测试、安全测试、playwright 测试 skills; 与后端整合, **打包合并成一个整体 skills 模块**。
2. 业务功能生成按 PACE 节奏流程走, 单测和 debug 按规定输出文档。
3. 再写一个**编排 skills 模块**, 调度前后端 skills 构建系统, 流程:
   接受需求清单 → 拆分 Sprint → checkpoint → 结合需求用系统内 skills 设计效果图 → checkpoint
   → 前端页面 demo (优先 mock 数据) + 本地发布运行 → checkpoint → 数据库表和 SQL 输出 **2 个分离文档**
   → checkpoint → 后端代码 → checkpoint → 后端单测+debug → 输出测试报告 → 前后端对接
   → review 代码 → playwright 测试 → 安全测试 → 原始功能清单核对需求确认 Sprint 完成情况
   → 输出: 需求完成情况 / 前后端完整测试报告 / **模型与 token 消耗情况** / 遗留问题与人工确认问题
   → checkpoint → 跟随指令发布。
4. 每个 checkpoint 不合格回滚到前面步骤继续 loop — **整个业务构建是 loop 工程**。
5. project-data-reader skill 也要完善。

## 当时权衡 (Claude 梳理, 用户已确认切片)

- **归属双层**: skill 本体 (系统无关) 住 Rlues; 约定包 (系统相关) 住各 quantum 仓库 docs/ai/convention-pack/。
  依据: S2 已实证 scaffold-module-gen 的"换脚手架=换约定包, skill 不改"分层 (quantum-backend
  sprints/2026-07-06-s2-scaffold-loop-verify/runtime-verify.md, 零返工 BUILD SUCCESS + G1-G4 全过)。
- **编排器不造第二状态机**: biz-delivery-loop 实现为 PACE Workflow 特化 (类比 ultracode),
  checkpoint = delivery-gate 家族扩展, 回滚 = rework/re-route 机制, 证据 = evidence-collector。
  两套 loop 抢 _index.md 写权必打架 — 这是硬约束。
- **流程 4 个洞** (Claude 补, 用户认可): ① API 契约冻结缺失 (效果图后冻结 OpenAPI, mock 从契约生成,
  对接=契约 diff); ② 效果图形态=HTML mockup+截图 (非设计稿图片); ③ playwright/安全测试需环境编排约定
  (FE+BE+DB 同起); ④ token 消耗统计需新 hook (usage 在 transcript, 现 evidence-collector 不收集)。
- **checkpoint 回滚协议**: 非"回起点" — 每个 CP 定义机器可验标准 (类 G1-G4) + 回滚目标表 + loop 轮次上限 + 超限升级人工。
- 执行方式: 双 session 并行 — Rlues session 跑 F1 (本 roadmap), quantum session 并行做约定包 (F2/F3 的 quantum 侧)。

## 逃生通道备注

若未来实现烂掉, 本文件 + roadmap/fullstack-delivery/ 足以弃码重生: 核心资产是 14 步流程定义、
4 洞补全、双层归属原则、回滚协议要求 — 皆与具体实现无关。
