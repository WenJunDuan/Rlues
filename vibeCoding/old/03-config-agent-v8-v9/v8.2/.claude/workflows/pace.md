# P.A.C.E. v2.1 路由编排

复杂度评估 → 路径选择 → 工具激活矩阵。

## 决策树

```
任务输入
  │
  ├─ 单文件 AND <30行?          → Path A (effort=low)
  ├─ 2-10文件 OR 30-500行?      → Path B (effort=medium)
  ├─ >10文件 OR 跨模块?         → Path C (effort=high)
  └─ 架构级 AND 可并行?         → Path D (effort=max)
```

Path D 触发 (≥2): >3模块 / 前后端可并行 / 预估>4h / --team。

---

## 工具激活矩阵

### VibeCoding Skills

| Skill | A | B | C | D |
|:---|:---|:---|:---|:---|
| brainstorm | — | R/D | R/D | R/D |
| cunzhi | 结束 | plan+end | 每阶段 | lead gates |
| tdd | — | 推荐 | 强制 | 强制 |
| verification | ✓ (基础) | ✓ (标准) | ✓ (严格) | ✓ (严格) |
| code-quality | — | ✓ | ✓ | ✓ |
| debugging | 按需 | 按需 | 按需 | 按需 |
| worktrees | — | — | ✓ | ✓ |
| context7 | 按需 | 按需 | 按需 | 按需 |
| knowledge | — | Rev | Rev | Rev |
| archive | — | — | Rev (>500K) | Rev (>500K) |
| agent-teams | — | — | — | ✓ |

### 官方 Plugins

| Plugin | A | B | C | D | 调用方式 |
|:---|:---|:---|:---|:---|:---|
| superpowers | — | ✓ | ✓ | ✓ | 自动: skill 内部触发 |
| code-review | — | Rev | Rev | Rev | 手动: `/review` |
| commit-commands | ✓ | ✓ | ✓ | ✓ | 自动: `git commit` 时触发 |
| feature-dev | — | P | P | P | 自动: P 阶段功能拆解 |
| frontend-design | — | 按需 | 按需 | 按需 | 自动: 检测前端文件时 |
| hookify | — | 按需 | 按需 | 按需 | 自动: 检测 React 组件时 |
| pr-review-toolkit | — | — | Rev | Rev | 手动: `/pr-review` |
| security-guidance | — | — | Rev | Rev | 自动: 代码审查时扫描 |
| plugin-dev | — | 按需 | 按需 | 按需 | 自动: 检测 plugin 代码时 |

### MCP 工具

| MCP | A | B | C | D | 调用方式 |
|:---|:---|:---|:---|:---|:---|
| sou (augment) | ✓ | ✓ | ✓ | ✓ | `sou.search("关键词")` |
| cunzhi | 结束 | plan+end | 每步 | lead gates | `cunzhi.confirm({checkpoint})` |
| deepwiki | — | R/D | R/D | R/D | `deepwiki.query("主题")` |

### Superpowers Skills

| SP Skill | A | B | C | D | 降级 (未安装时) |
|:---|:---|:---|:---|:---|:---|
| brainstorming | — | R/D | R/D | R/D | AI 直接苏格拉底提问 |
| writing-plans | — | P | P | P | AI 直接微任务拆解 |
| tdd | — | E推荐 | E强制 | E强制 | AI 直接 RED-GREEN-REFACTOR |
| subagent-driven-dev | — | E | E | E | 顺序执行 |
| verification-before-completion | ✓ | ✓ | ✓ | ✓ | AI 直接执行验证清单 |
| requesting-code-review | — | Rev | Rev | Rev | AI 直接六维审查 |
| debugging | 按需 | 按需 | 按需 | 按需 | AI 直接四阶段调试 |

---

## 路径配置

### Path A — Quick Fix

```yaml
riper: R → E → V
effort: low
tdd: 跳过
cunzhi: 仅结束
worktree: 否
verification: 基础 (测试+Lint+无残留)
plugins: commit-commands
commit策略: 改完直接 commit
duration: <1h
```

### Path B — Planned Development

```yaml
riper: R → D → P → C → E → V → Rev
effort: medium
tdd: 推荐 (--no-tdd 可跳)
cunzhi: plan + end
worktree: 建议新分支
verification: 标准 (含 plan 覆盖+验收标准)
plugins: superpowers, code-review, feature-dev, commit-commands
commit策略: 每个 TASK 完成后 commit
duration: 2-8h
```

### Path C — System Development

```yaml
riper: 完整 7 步 (九步展开, 每步寸止)
effort: high
tdd: 强制
cunzhi: 每阶段
worktree: 自动 (skill/worktrees)
verification: 严格 (含覆盖率+安全+文件大小)
plugins: 全部
commit策略: 每个 GREEN 后 commit (小步提交)
duration: 数天
```

### Path D — Agent Teams

```yaml
riper: Lead(R→D→P→C) → Teams(E) → Lead(V→Rev)
effort: max
tdd: 强制 (每个 teammate)
cunzhi: Lead gates
worktree: worktree + 子分支
verification: 严格
plugins: 全部
skills: agent-teams
requires: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
commit策略: 每个 teammate 独立 commit, Lead merge
duration: 数小时-数天
降级: Agent Teams 失败 → Path C
```
