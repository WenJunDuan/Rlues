# P.A.C.E. v2.1 路由编排 (Codex CLI)

复杂度评估 → 路径选择 → 工具激活矩阵。
Codex 无 Path D，`--team` 降级 Path C。

## 决策树

```
任务输入
  │
  ├─ 单文件 AND <30行?          → Path A (effort=low)
  ├─ 2-10文件 OR 30-500行?      → Path B (effort=medium)
  ├─ >10文件 OR 跨模块?         → Path C (effort=high)
  └─ --team?                     → 降级 Path C (Codex 无 Agent Teams)
```

---

## 工具激活矩阵

### VibeCoding Skills

| Skill | A | B | C |
|:---|:---|:---|:---|
| brainstorm | — | R/D | R/D |
| cunzhi | 结束 | plan+end | 每阶段 |
| tdd | — | 推荐 | 强制 |
| verification | ✓ (基础) | ✓ (标准) | ✓ (严格) |
| code-quality | — | ✓ | ✓ |
| debugging | 按需 | 按需 | 按需 |
| worktrees | — | — | ✓ |
| context7 | 按需 | 按需 | 按需 |
| knowledge | — | Rev | Rev |
| archive | — | — | Rev (>500K) |

### MCP 工具

| MCP | A | B | C | 调用方式 |
|:---|:---|:---|:---|:---|
| sou (augment) | ✓ | ✓ | ✓ | `sou.search("关键词")` |
| cunzhi | 结束 | plan+end | 每步 | `cunzhi.confirm({checkpoint})` |
| deepwiki | — | R/D | R/D | `deepwiki.query("主题")` |
| chrome-devtools | 按需 | 按需 | 按需 | Codex 前端调试专属 |

### Superpowers Skills

| SP Skill | A | B | C | 降级 (未安装时) |
|:---|:---|:---|:---|:---|
| brainstorming | — | R/D | R/D | AI 直接苏格拉底提问 |
| writing-plans | — | P | P | AI 直接微任务拆解 |
| tdd | — | E推荐 | E强制 | AI 直接 RED-GREEN-REFACTOR |
| subagent-driven-dev | — | E | E | 顺序执行 |
| verification-before-completion | ✓ | ✓ | ✓ | AI 直接执行验证清单 |
| requesting-code-review | — | Rev | Rev | AI 直接六维审查 |
| debugging | 按需 | 按需 | 按需 | AI 直接四阶段调试 |

### Claude Code Plugin 替代映射

| Claude Code Plugin | Codex 替代 | 替代位置 |
|:---|:---|:---|
| code-review | SP requesting-code-review | Rev 阶段 |
| commit-commands | 手动 Conventional Commits | E 阶段 |
| feature-dev | SP writing-plans | P 阶段 |
| frontend-design | 无 (直接编码) | E 阶段 |
| hookify | 无 (直接编码) | E 阶段 |
| pr-review-toolkit | SP requesting-code-review | Rev 阶段 |
| security-guidance | skill/code-quality 手动安全检查 | Rev 阶段 |

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
commit: 改完直接 commit (手动 Conventional)
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
commit: 每个 TASK 完成后 (手动 Conventional)
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
commit: 每个 GREEN 后 (手动 Conventional, 小步提交)
duration: 数天
```
