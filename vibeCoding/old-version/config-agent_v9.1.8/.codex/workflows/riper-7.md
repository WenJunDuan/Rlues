# RIPER-7 阶段编排 v9.1.8

## 每阶段进入前 (通用)
1. 核心问题是什么?
2. 项目有类似实现? → 搜索项目代码
3. 库 API 确定? → context7 skill / web search 查文档
4. .ai_state/knowledge.md + lessons.md 有相关经验?

---

## R₀ 需求精炼 (Path B+)
**技能**: brainstorm skill → 向用户提问 (技术细节、边界情况、非功能需求)
**产出**: .ai_state/design.md (Spec: MUST/SHOULD/COULD + 验收标准)
**门控**: 暂停等用户确认方向

## R 技术调研 (Path B+)
**动手**: 搜索项目代码找可复用实现 + web search 查库版本和 API
**产出**: design.md 追加技术方案 (接口定义、数据流、依赖)
**要回答**: 可复用代码? 需要新依赖? 性能瓶颈?

## D 方案定稿 (Path B+)
**特有问题**: 接口是否最小化? 错误处理完整? 有更简单方案?
**产出**: design.md 定稿 (锁定, 不再改)
**门控**: 暂停等用户确认方案

## P 计划制定 (Path B+)
**技能**: plan-first skill → 分解 Task (每个 2-5min, 含文件列表+依赖)
**产出**: .ai_state/plan.md

### Plan Review (P 内嵌)
产出后、确认前审查:
- Path B: 自审 — "初级工程师能执行? 粒度? 依赖清楚? 文件准确? 验收可测?"
- Path C+: spawn_agent(validator) 审查计划
- 不合格 → 修改 plan.md 再审

**Codex原生**: /plan 进入规划模式
**门控**: 暂停等用户确认计划

## E 执行实现 (All Paths)
**规则**: 铁律 #2 — 先测后码 (→ tdd skill)

### Sisyphus 循环 (不完成不停止)
```
重复:
  1. 读 plan.md → 找到第一个 [ ]
  2. 执行该 Task (tdd: RED→GREEN→REFACTOR)
  3. Micro-review:
     - Spec 合规: 做的是 design.md 要求的吗? 多做/少做?
     - 代码质量: 类型严格? 函数合理? 错误处理?
     Path B: 自检 | Path C+: spawn_agent(validator) 审查
  4. 不合格 → 当场修复
  5. 标记 [x] + git commit + 更新 status.md
  → 直到 plan.md 无 [ ]
```

**子代理 (Path C+)**: spawn_agent 并行实现, wait_agent 等待完成

## T 测试验证 (All Paths)
**全局审查** — 跨 Task 集成测试 + 安全扫描
**技能**: verification skill → 全量测试 + 覆盖率
**技能**: code-review skill → 代码审查 (含通用质量标准)
**可选**: LSP diagnostics (如可用) / ast-grep (如可用)
**Codex原生**: /review 触发代码审查
**产出**: .ai_state/quality.md

## V 交付归档 (Path B+)
**技能**: kaizen skill → 复盘写入 knowledge.md + lessons.md
**门控**: 暂停等用户确认交付

---

## 工具箱 (任何阶段按需)
| 工具 | 用途 |
|------|------|
| context7 skill / web search | 查库文档 |
| spawn_agent / wait_agent | 子代理并行 (Path C+) |
| /plan | Codex 规划模式 |
| /review | Codex 代码审查 |
| LSP diagnostics | 类型信息 (如可用) |
| ast-grep | AST级搜索 (如可用) |

## 状态文件生命周期
```
status.md:      全程维护 (当前阶段+进度)
design.md:      R₀写入 → R追加 → D定稿
plan.md:        P写入 → E逐项[x] → V归档
quality.md:     T写入 (验证+审查报告)
conventions.md: 初始化写入, 按需更新
knowledge.md:   V追加 (代码库知识)
lessons.md:     V追加 (经验教训)
```
