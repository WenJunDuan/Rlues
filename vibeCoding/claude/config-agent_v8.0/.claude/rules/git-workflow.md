# Git Workflow Rules

## Commit Message
```
type(scope): description

type: feat|fix|refactor|docs|test|chore
scope: 模块名
description: 简明描述变更
```

## Branch
- main/master: 生产分支
- dev/develop: 开发分支
- feature/*: 功能分支
- fix/*: 修复分支

## 提交前检查
- 无 console.log
- 无调试代码
- 无 TODO 标记
- TypeScript 编译通过
