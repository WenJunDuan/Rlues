---
name: git-workflow
description: Git工作流规范，分支策略和提交规范
trigger: 代码修改完成后
---

# Git Workflow Skill

> **版本控制是工程的基石**
> 清晰的提交历史 = 可追溯的项目演进

---

## 🌿 分支策略

### 标准分支

| 分支 | 用途 | 保护 |
|:---|:---|:---|
| `main` | 生产代码 | ✅ 保护 |
| `develop` | 开发主线 | ✅ 保护 |
| `feature/*` | 功能开发 | ❌ |
| `bugfix/*` | Bug修复 | ❌ |
| `hotfix/*` | 紧急修复 | ❌ |
| `release/*` | 发布准备 | ❌ |

### 分支命名

```bash
# 功能分支
feature/user-authentication
feature/payment-integration

# Bug修复
bugfix/login-redirect-issue
bugfix/memory-leak

# 热修复
hotfix/critical-security-patch
```

### 分支流程

```
main ──────────────────────────────────────────────▶
  │                                    ↑
  └──▶ develop ────────────────────────┼───────────▶
          │         ↑        ↑         │
          └──▶ feature/xxx ──┘         │
                                       │
          └──▶ bugfix/xxx ─────────────┘
```

---

## 📝 提交规范

### Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 用途 |
|:---|:---|
| `feat` | 新功能 |
| `fix` | Bug修复 |
| `docs` | 文档更新 |
| `style` | 格式调整（不影响代码） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

### 示例

```bash
# 简单提交
feat(auth): add login validation

# 带body
fix(api): handle null response from server

The API sometimes returns null instead of empty array.
Added null check to prevent crash.

# 带breaking change
feat(db)!: change user schema

BREAKING CHANGE: user.name is now split into firstName and lastName
```

### 提交检查清单

- [ ] 提交信息是否清晰？
- [ ] 是否只包含相关修改？
- [ ] 是否需要拆分成多个提交？
- [ ] 是否影响现有功能？

---

## 🔄 工作流程

### 1. 开始新功能

```bash
# 1. 从 develop 创建分支
git checkout develop
git pull origin develop
git checkout -b feature/user-profile

# 2. 开发...

# 3. 提交
git add .
git commit -m "feat(profile): add user avatar upload"

# 4. 推送
git push origin feature/user-profile

# 5. 创建 PR/MR
```

### 2. 修复 Bug

```bash
# 1. 从 develop 创建分支
git checkout -b bugfix/login-issue develop

# 2. 修复...

# 3. 提交
git commit -m "fix(auth): handle expired token correctly"

# 4. 合并回 develop
git checkout develop
git merge bugfix/login-issue
```

### 3. 紧急修复

```bash
# 1. 从 main 创建
git checkout -b hotfix/security-patch main

# 2. 修复...

# 3. 合并到 main 和 develop
git checkout main
git merge hotfix/security-patch
git checkout develop
git merge hotfix/security-patch
```

---

## 🔙 回滚策略

### 回滚单个提交

```bash
# 创建新提交来撤销
git revert <commit-hash>
```

### 回滚到特定版本

```bash
# 软回滚（保留修改）
git reset --soft <commit-hash>

# 硬回滚（丢弃修改）
git reset --hard <commit-hash>
```

### 回滚合并

```bash
git revert -m 1 <merge-commit-hash>
```

---

## 📋 PR/MR 检查清单

创建 Pull Request 前：

- [ ] 代码已本地测试
- [ ] 提交历史清晰
- [ ] 无调试代码（console.log）
- [ ] 已更新文档（如需要）
- [ ] 已添加测试（如需要）
- [ ] 符合代码规范

PR 描述模板：

```markdown
## 变更说明
[描述做了什么]

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 重构
- [ ] 文档

## 测试
- [ ] 单元测试通过
- [ ] 手动测试通过

## 截图（如有UI变更）
[截图]

## 相关 Issue
Closes #123
```

---

## 🛡️ 保护规则

### main 分支
- ❌ 禁止直接推送
- ✅ 需要 PR 审查
- ✅ 需要 CI 通过
- ✅ 需要 1+ 审批

### develop 分支
- ❌ 禁止 force push
- ✅ 需要 CI 通过

---

## ⚠️ 禁止操作

```bash
# ❌ 禁止在 main 上直接修改
git checkout main
git commit ...  # 禁止！

# ❌ 禁止 force push 保护分支
git push -f origin main  # 禁止！

# ❌ 禁止提交敏感信息
git add .env  # 检查 .gitignore！
```

---

## 🔗 与开发流程集成

| 阶段 | Git 操作 |
|:---|:---|
| P (Plan) | 创建 feature 分支 |
| E (Execute) | 多次小提交 |
| R2 (Review) | 创建 PR，请求审查 |
| 通过 | 合并到 develop |

---

**核心**: 小步提交、清晰历史、保护主干 | **规范**: Conventional Commits
