# RIPER-7 阶段编排 v9.1.7

## 每阶段进入前 (通用)

1. **定义**: 这一步要解决的核心问题是什么?
2. **搜索**: 项目里有没有类似实现?
3. **查文档**: 用到的库 API 确定吗? → 用 context7 skill 或 web search
4. **历史**: .ai_state/knowledge.md + lessons.md 有相关经验吗?

---

## R₀ 需求精炼 (Path B+)

**读**: 用户需求
**技能**: brainstorm skill → 访谈用户, 明确需求
**产出**: .ai_state/design.md (Spec: MUST/SHOULD/COULD + 验收标准)
**门控**: 暂停等用户确认方向

## R 技术调研 (Path B+)

**读**: design.md
**动手**: 搜索相关代码 + 查库版本和 API
**产出**: design.md 追加技术方案
**要回答**: 有没有可复用的现有代码? 需要新依赖吗?

## D 方案定稿 (Path B+)

**读**: design.md
**特有问题**: 接口是否最小化? 错误处理是否完整? 有没有更简单的方案?
**产出**: design.md 定稿
**门控**: 暂停等用户确认方案

## P 计划制定 (Path B+)

**读**: design.md (定稿)
**技能**: plan-first skill
**产出**: .ai_state/plan.md (任务清单+预估+依赖)
**门控**: 暂停等用户确认计划
**Codex原生**: 可用 /plan 进入规划模式

## E 执行实现 (All Paths)

**读**: plan.md (Path A 可跳过)
**规则**: 铁律 #2 — 先写测试再写实现 (→ tdd skill)
**子代理 (Path C+)**: 用 spawn_agent 并行实现不同模块, wait_agent 等待完成
**产出**: 代码 + 测试, status.md 更新进度

## T 测试验证 (All Paths)

**技能**: verification skill → 运行测试
**技能**: code-review skill → 审查代码
**Codex原生**: 可用 /review 触发代码审查
**产出**: .ai_state/quality.md

## V 交付归档 (Path B+)

**技能**: kaizen skill → 复盘
**产出**: 更新 knowledge.md + lessons.md
**门控**: 暂停等用户确认交付

---

## 工具箱 (任何阶段按需使用)

| 工具           | 用途                         |
| -------------- | ---------------------------- |
| context7 skill | 查询库/框架文档              |
| web search     | 搜索最新信息                 |
| spawn_agent    | 启动子代理并行工作 (Path C+) |
| wait_agent     | 等待子代理完成               |
| /plan          | 进入规划模式                 |
| /review        | 代码审查                     |

## 状态文件生命周期

```
status.md:  全程维护 (当前阶段+进度)
design.md:  R₀写入 → R追加 → D定稿
plan.md:    P写入 → E逐项完成 → V归档
quality.md: T写入 (验证+审查报告)
conventions.md: 初始化时写入, 按需更新
knowledge.md:   V阶段追加 (代码库知识)
lessons.md:     V阶段追加 (经验教训)
```
