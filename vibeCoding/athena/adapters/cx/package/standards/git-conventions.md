---
effort: low
attach_to_stages: [ship]
attach_to_subagents: []
---

<important if="committing, branching, or opening PR">
# Git Conventions · Git 约定

> 适用于所有 commit / branch / PR 操作.
> ship stage 强制注入本规则.

## Commit Message 格式 (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

### type (必填, 限定枚举)

| type | 用途 |
|---|---|
| feat | 新功能 |
| fix | bug 修复 |
| refactor | 重构 (不改变功能) |
| perf | 性能优化 |
| docs | 仅文档变更 |
| test | 仅测试变更 |
| chore | 构建脚本 / 配置 / 依赖更新 |
| ci | CI 配置变更 |
| style | 仅格式调整 (空格 / 分号) |
| revert | 回滚 |

### scope (可选)

模块名或目录名 (`auth` / `api` / `ui` / `db`). 不要用泛词如 "code".

### subject (必填)

- ≤ 50 字符
- 祈使句, 不加句号
- 首字母小写

### body (可选)

- 解释 **why** 和 **what**, 不是 **how** (how 看代码)
- 多行用空行分隔
- 引用 issue 用 `Refs #123` 或 `Closes #123`

### 示例

```
feat(auth): 添加 JWT refresh token 机制

之前 access token 24h 过期, 用户需要重新登录, 体验差.
现在引入 refresh token (30d), access token 缩到 1h.

Closes #456
```

## Branch 命名

格式: `<type>/<short-description>` 或 `<type>/<issue-id>-<short>`

```
feat/jwt-refresh
fix/123-login-redirect-bug
refactor/api-error-handling
chore/upgrade-react-18
```

禁止:
- `feature/xxx`, `bugfix/xxx` (用 feat / fix 不是 feature / bugfix)
- 中文 branch 名
- 过长 (≤ 40 字符)

## PR Description

### 必须包含

```markdown
## 变更类型
[ ] feat  [ ] fix  [ ] refactor  [ ] docs  [ ] chore

## 变更说明
(简述本 PR 做了什么)

## 关联 Issue
Closes #xxx (or Refs #xxx)

## 验证步骤
1. ...
2. ...

## 检查清单
- [ ] 已运行测试 (npm test / pytest 等)
- [ ] 已通过 lint
- [ ] 已更新文档 (如适用)
- [ ] 已经 polish (Refactor/System 路径)
```

### 不要

- 单 line description ("修一下 bug")
- 没有验证步骤
- 关联 issue 用 "see #123" 不写 Closes (issue 不会自动关闭)

## 强制不要的操作

- `git push --force origin main` / `master` (force push 受保护分支)
- `git commit --amend` 推过远程的 commit (除非本地分支)
- `git reset --hard` 公共分支
- 包含密钥 / token 的 commit (即使后续 amend, history 也会留痕)

## 例外

- 文档 typo / 注释 typo: 可省略 body, 直接 `docs(readme): fix typo`
- 紧急 hotfix: 可降低 PR 模板要求, 但必须 followup PR 补充
</important>
