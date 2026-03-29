# 项目规范

> 由 /vibe-init 检测填充, 按需手动补充

## 基本信息
- 语言: (检测 package.json→TypeScript | Cargo.toml→Rust | go.mod→Go | pyproject.toml→Python)
- 框架: (检测 dependencies 中的 react/vue/express/fastapi 等)
- 测试命令: (检测 package.json scripts.test | cargo test | go test | pytest)
- 包管理器: (检测 lock 文件: package-lock→npm | yarn.lock→yarn | pnpm-lock→pnpm)

## 目录结构
(初始化时 ls 项目根目录生成)

## Commit 格式
feat|fix|refactor|docs|test|chore: 简述

## 项目特有规则
(按需添加, 例如:)
- API 返回格式: { code: number, data: T, message: string }
- 状态管理: 用 Zustand 不用 Redux
- 组件命名: PascalCase, 文件名与组件名一致
