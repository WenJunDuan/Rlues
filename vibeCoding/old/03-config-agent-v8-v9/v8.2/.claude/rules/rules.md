# 项目规则

只保留 AI 不知道的项目约定。常识省略。

## 编码

- TypeScript 优先，any 零容忍
- 函数 <50 行，嵌套 <3 层
- 错误用具体类型，不用 `catch(e: any)`
- import 顺序: 外部库 → 内部模块 → 相对路径 → 类型

## Git

- 分支: `feature/vibe-{id}-{desc}`, `fix/vibe-{id}-{desc}`
- Commit: Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`)
- Path C/D: worktree 隔离 (加载 worktrees skill)
- 不直接推 main

## 测试

- Path B: 60% 覆盖率
- Path C: 80% 覆盖率
- Path D: 85% 覆盖率
- 测试文件: `*.test.ts` / `*.spec.ts` 与源文件同目录

## 安全

- 敏感信息走环境变量，不硬编码
- 公共接口验证输入
- SQL 用参数化查询
