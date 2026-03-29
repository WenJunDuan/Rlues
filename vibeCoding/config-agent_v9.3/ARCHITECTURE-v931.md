# VibeCoding Kernel v9.3.1 — 架构演进计划

> 基线: v9.3.0 (插件栈+hooks+配置 OK, 但提示词被过度精简)
> 参考: v8.9 (提示词质量标杆, 约束充分, agent 可执行)
> 目标: v8.9 的提示词质量 + v9.3.0 的插件栈/配置/双Agent

---

## 一、问题诊断: v9.3.0 vs v8.9

| 维度       | v8.9                                                                 | v9.3.0                            | 问题                                                     |
| ---------- | -------------------------------------------------------------------- | --------------------------------- | -------------------------------------------------------- |
| CLAUDE.md  | ~100行, 身份+铁律+三层分工+工具表+降级+状态管理+Agent Teams+新手指引 | ~65行, 插件表+独有能力表+框架地图 | **缺身份、铁律、三层分工、降级通则、状态管理、新手指引** |
| riper-7.md | ~150行, 统一工具调度表+每阶段(💡做什么+🔧工具+步骤1234)+Path分级     | ~50行, 每阶段2-3行                | **agent不知道每步做什么、用什么工具、什么顺序**          |
| pace.md    | ~80行, 5维判定表+每Path详细加载+路由输出格式+新手解释                | ~12行, 一个表格                   | **agent不知道怎么判定路径、加载什么**                    |
| AGENTS.md  | ~80行, 同CLAUDE.md结构                                               | ~45行, 精简版                     | **同上**                                                 |
| Skills     | 13个, 每个15-30行有步骤                                              | 7个, 每个5-15行                   | **可接受 (插件覆盖了)**                                  |

### 根因

v9.1.7 开始追求"token效率"砍内容, 到 v9.3.0 砍过头了。
v8.9 的"丰富"不是冗余——它是 **agent 的操作手册**。没有步骤, agent 就即兴发挥。

---

## 二、v9.3.1 设计原则

1. **v8.9 的丰富度 + v9.3.0 的插件栈** — 不是二选一
2. **三层分工清晰化** — superpowers/ECC/官方plugins 做HOW, MCP做执行, VibeCoding做WHEN/WHERE
3. **每个阶段有具体步骤** — agent 读完知道 1→2→3 做什么
4. **降级链完整** — 每个工具/插件不可用时的替代方案
5. **新手友好** — 说"做个登录功能"就能跑起来
6. **双Agent编排显式化** — CC↔Codex 的调度在 riper-7 中明确标注

---

## 三、文件级变更

### 3.1 CLAUDE.md (从 ~65行 → ~120行)

恢复 v8.9 的:

- ✅ 身份声明 (INTJ 工程化系统)
- ✅ 铁律 5 条 (从 v8.9 继承, 适配插件栈)
- ✅ 三层分工表 (Plugins/MCP/VibeCoding)
- ✅ 工具注册表 (Plugins + MCP + 降级通则)
- ✅ 分级加载表 (Path → 加载内容 → tokens)
- ✅ 状态管理目录树 (.ai_state/ + .knowledge/ 如用户使用)
- ✅ Agent Teams (Path C+)
- ✅ 新手指引

新增/保留 v9.3.0 的:

- ✅ 插件栈 enabledPlugins 说明
- ✅ VibeCoding 独有能力 (Reflexion/Kaizen/4级Gate/验收标准/LLM-as-Judge)
- ✅ 框架地图
- ✅ Fallback 策略 (gstack/superpowers/ECC 不可用时)

### 3.2 riper-7.md (从 ~50行 → ~160行)

恢复 v8.9 的:

- ✅ 统一工具调度表 (阶段 × Skill × Plugin × MCP × 状态文件)
- ✅ 每阶段: 💡做什么 + 🔧自动使用 + ⏭️下一阶段
- ✅ 每阶段具体步骤 (1,2,3...)
- ✅ Path 分级说明 (Path A 简化/跳过的标注)

新增/适配:

- ✅ 每阶段标注插件命令 (/superpowers:brainstorm, /codex, /code-review 等)
- ✅ E 阶段三级降级: /codex委托 → superpowers execute → 手动TDD
- ✅ 内联 fallback (每步插件不可用的替代)
- ✅ Path A 独立段

### 3.3 pace.md (从 ~12行 → ~80行)

恢复 v8.9 的:

- ✅ 5维路由判定表 (文件数/时间/关键词/描述长度/需求数)
- ✅ 每 Path 详细: 加载内容 + RIPER节点 + skills列表 + 确认点
- ✅ 路由输出格式示例
- ✅ 新手解释 (💡 给新手: 这是"改一行CSS"级别)

适配:

- ✅ 加载内容更新为插件栈 + VibeCoding skills
- ✅ Codex 参与度按 Path 分级

### 3.4 AGENTS.md (从 ~45行 → ~80行)

同 CLAUDE.md 结构, Codex 适配:

- ✅ 身份 + 铁律
- ✅ 工具注册表 (Codex 侧 MCP + plugins)
- ✅ 分级加载
- ✅ 并行执行说明
- ✅ 模型表
- ✅ 被 CC 调用时的行为

### 3.5 Skills — 微调不重写

| Skill           | 变更 |
| --------------- | ---- |
| code-review     | 不变 |
| verification    | 不变 |
| kaizen          | 不变 |
| reflexion       | 不变 |
| security-review | 不变 |
| context7        | 不变 |
| e2e             | 不变 |

Skills 已经在 v9.2.2 迭代过, 质量够用。问题出在 CLAUDE.md/riper-7/pace 太薄。

### 3.6 Hooks/Commands/Agents/Templates/Config

**不改。** v9.3.0 已经修正了所有配置问题 (嵌套hooks格式, execFileSync, JSON decision output, enabledPlugins, 真实config.toml)。

---

## 四、不做的事

- ❌ 不恢复已删的 brainstorm/plan-first/debugging/finish-branch skills (superpowers覆盖)
- ❌ 不恢复 codex-comm/codex-review (gstack替代)
- ❌ 不恢复 mcp-deepwiki (用户不用, 保留 context7)
- ❌ 不重写 hooks/config (已修正)
- ❌ 不增加新 skills (现有 7 个 + 插件覆盖已足够)

---

## 五、预估

| 指标       | v9.3.0 | v9.3.1  | 变化              |
| ---------- | ------ | ------- | ----------------- |
| CLAUDE.md  | ~65行  | ~120行  | +85% (恢复丰富度) |
| riper-7.md | ~50行  | ~160行  | +220% (恢复步骤)  |
| pace.md    | ~12行  | ~80行   | +567% (恢复判定)  |
| AGENTS.md  | ~45行  | ~80行   | +78%              |
| 其余文件   | 不变   | 不变    | 0%                |
| CC 总行数  | ~800行 | ~1100行 | +38%              |
| CX 总行数  | ~363行 | ~500行  | +38%              |

行数回到 v8.9 水平, 但内容是 v9.3.0 的插件栈架构。

---

## 六、实施顺序

```
Phase 1: CLAUDE.md + AGENTS.md 重写 (恢复丰富度 + 插件栈)
Phase 2: riper-7.md 重写 (恢复步骤 + 工具调度表 + 双Agent)
Phase 3: pace.md 重写 (恢复判定 + 分级加载)
Phase 4: 审计 (框架地图准确性 + agent视角走场景)
Phase 5: 打包交付
```
