# Hotfix：9.9.9 电宝体（非新版本）

目标：在 9.9.9 原包恢复电报体/电宝体；补文件清单与产出声明。不升 9.9.10。
允许写集：`vibeCoding/{claude,codex}/9.9.9` 提示词/模板/doc-style；本 sprint 文书。不改 hook/validator/门禁字段名。不安装。
完成条件：热路径去复述；doc-style 产出声明落地；CC/CX 语义对齐；门禁标题仍可解析。

分诊：用户显式 Hotfix + 文案完善。候选 Feature 因「非迭代、原包更新」否决。conf=1.0。
旧任务恢复：`../2026-09-07-pace-task-triage-hotfix/session-log.md`；父 System 未完成。

## 文件清单

### 本轮改（P0 热路径 + P1 产出声明）

| 层 | CC | CX |
|---|---|---|
| 常驻根 | `.claude/CLAUDE.md` | `.codex/AGENTS.md` |
| 产出纪律 | `.claude/rules/doc-style.md` | `.codex/standards/doc-style.md` |
| 路由热路径 | `skills/pace/SKILL.md` | 同 |
| 分诊 | `skills/athena-dev/SKILL.md` | 同 |
| 复利 | `skills/compound/SKILL.md` | 同 |
| 阶段义务 | `skills/pace/references/stages.md` | 同（原生入口差一行） |
| 审查提示 | `skills/athena-review/REVIEW.md` | 同 |
| 角色 | `agents/{generator,reviewer,polish-worker,architect}.md` | `agents/{generator,reviewer,polish_worker,architect}.toml` |
| 模板 | `pace/templates/sprints/{design,brainstorm,cleanup-pass,route-note}.md` `reviews/implementation-review.md` | 同 |
| compound 模板 | `compound/templates/{learning,trick,decision,explore}.md` | 同 |
| 发行说明 | `CHANGELOG.md` 9.9.9 条 | 同 |

权威产出声明只写在 doc-style；其余引用。

### 本轮不改（P2 / 机械）

- `gate-contracts.md` 字段/命令；`execution-contracts.md`；hooks；validator
- quantum-* / biz-delivery / deps-check playbook
- CX `docs_researcher.toml` `pr_explorer.toml`（合同冲突，非文风）
- 旧版 `vibeCoding/*/9.9.0–9.9.8`
- 安装态 `~/.claude` `~/.codex`（改包 ≠ 已装）

### 永不动

门禁标题：`## 验收标准` / `## Done Contract` / `## 测试场景`；review frontmatter；tdd 九字段；AC ID。

## 实测

| 文件 | 前 | 后 |
|---|---:|---:|
| CC pace/SKILL.md | 6524 | 3230 |
| CX pace/SKILL.md | 6760 | 3504 |
| athena-dev/SKILL.md | 4773 | 2681 |
| compound/SKILL.md | 4468 | 1658 |
| CX architect.toml | 2811 | 1092 |
| CLAUDE.md | 4003 | 4059 |
| AGENTS.md | 4327 | 4386 |
| stages.md | ~9574 | ~9506 |

产出声明权威: CC `rules/doc-style.md` · CX `standards/doc-style.md`。
validator: `package_checks_pass=59 fail=1`。唯一 FAIL=`CC agents have maxTurns=70`（此前已从 frontmatter 去掉, 70 轮写在正文; 非本文风改动引入）。未安装、未推送。
