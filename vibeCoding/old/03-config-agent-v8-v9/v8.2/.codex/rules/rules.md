# 项目规则

## 代码规范

- TypeScript 优先，any 零容忍
- 函数 <50 行，嵌套 <3 层
- 公共接口必须输入验证
- 错误处理完整覆盖

## Git 规范

- 分支: `feature/vibe-{id}-{desc}`
- Commit: Conventional Commits (手动格式化)
  - `feat:` 新功能
  - `fix:` 修复
  - `refactor:` 重构
  - `test:` 测试
  - `docs:` 文档
- 不直接推 main
- 敏感信息走环境变量，不硬编码

## 文件规范

- 组件 <200 行
- 单文件 <500 行
- 无注释掉的代码块
- 无 console.log / debugger 残留
