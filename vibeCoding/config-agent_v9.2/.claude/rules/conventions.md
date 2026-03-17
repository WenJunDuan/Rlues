# 项目规范 (仅列 AI 不知道的项目特定规范)

## Git
- prefix: feat|fix|refactor|docs|test|chore|perf|ci
- scope 可选: feat(auth): add JWT middleware
- 一个 commit 一个逻辑变更, 不混合

## 代码组织 (根据项目自定义)
- 目录结构: src/ tests/ docs/ scripts/
- 测试文件: *.test.ts / *.spec.ts, 与源码同目录或 tests/ 镜像
- 环境变量: .env.example 记录所有变量, .env 在 .gitignore

## TypeScript (根据项目自定义)
- 严格模式: strict: true
- 导入顺序: 外部库 → 内部模块 → 类型 → 相对路径
- 错误处理: 自定义 Error class, 不用 string throw

## 命名 (根据项目自定义)
- 文件: kebab-case (user-service.ts)
- 类/接口: PascalCase
- 函数/变量: camelCase
- 常量: UPPER_SNAKE_CASE
- 数据库: snake_case
