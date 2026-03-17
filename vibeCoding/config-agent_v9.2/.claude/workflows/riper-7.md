# RIPER-7 阶段编排 v9.1.7

## 每阶段进入前 (通用)
1. **定义**: 这一步要解决的核心问题是什么?
2. **搜索**: 项目里有没有类似实现? → augment-context-engine
3. **查文档**: 用到的库 API 确定吗? → context7 skill / mcp-deepwiki
4. **历史**: .ai_state/knowledge.md + lessons.md 有相关经验吗?

---

## R₀ 需求精炼 (Path B+)
**读**: 用户需求
**技能**: brainstorm skill → 用 AskUserQuestion 访谈用户
**产出**: .ai_state/design.md (Spec: MUST/SHOULD/COULD + 验收标准)
**门控**: cunzhi [DESIGN_DIRECTION] → 用户确认方向

## R 技术调研 (Path B+)
**读**: design.md
**动手**: augment-context-engine 搜相关代码 + context7 查库版本
**产出**: design.md 追加技术方案 (接口定义、数据流、依赖)
**要回答**: 有没有可复用的现有代码? 需要新依赖吗? 性能瓶颈在哪?

## D 方案定稿 (Path B+)
**读**: design.md
**特有问题**: 接口是否最小化? 错误处理是否完整? 有没有更简单的方案?
**产出**: design.md 定稿 (锁定方案, 不再改动)
**门控**: cunzhi [DESIGN_LOCKED]

## P 计划制定 (Path B+)
**读**: design.md (定稿)
**技能**: plan-first skill
**产出**: .ai_state/plan.md (任务清单, 每个任务有预估时间+文件列表+依赖)
**门控**: cunzhi [PLAN_CONFIRMED]
**CC特性**: 可用 /plan {摘要} 进入规划模式

## E 执行实现 (All Paths)
**读**: plan.md (Path A 可跳过, 直接执行)
**规则**: 铁律 #2 — 先写测试再写实现 (→ tdd skill)
**工具**: 复杂任务用 /effort high
**子代理 (Path C+)**: Agent(builder) 实现, Agent(explorer) 并行调研
**产出**: 代码 + 测试, status.md 更新进度
**每个 Task 完成后**: git add + commit (conventional commits)

## T 测试验证 (All Paths)
**技能**: verification skill → 运行测试 + 检查覆盖率
**技能**: code-review skill → 审查代码质量 + 安全
**子代理 (Path C+)**: Agent(validator) 审查
**产出**: .ai_state/quality.md (验证报告)
**要回答**: 测试真的覆盖了关键路径吗? 作为 reviewer 我会质疑哪里?

## V 交付归档 (Path B+)
**技能**: kaizen skill → 复盘, 写入 knowledge.md + lessons.md
**门控**: cunzhi [DELIVERY_CONFIRMED]
**产出**: 更新 knowledge.md (代码库知识) + lessons.md (经验教训)
**收尾**: 清理 status.md, 标记任务完成

---

## 工具箱 (任何阶段按需使用)
| 工具 | 用途 |
|------|------|
| augment-context-engine | 搜索项目代码 |
| mcp-deepwiki | 查询库/框架文档 |
| context7 CLI | 按需拉取库文档到上下文 |
| cunzhi MCP | 发起人工确认检查点 |
| Agent(builder) | 子代理: 实现+测试 (Path C+) |
| Agent(validator) | 子代理: 审查+验证 (Path C+) |
| Agent(explorer) | 子代理: 调研 (background) |
| /effort high | 复杂任务前提升推理深度 |
| /plan {摘要} | 进入规划模式 |
| /loop {间隔} {命令} | 持续监控 (如测试watch) |

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
