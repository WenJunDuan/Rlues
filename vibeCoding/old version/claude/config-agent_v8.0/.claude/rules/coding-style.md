# Coding Style Rules

## 通用
- 函数 <50 行
- 嵌套 <3 层
- 组件 <200 行
- 单文件 <500 行
- 命名反映本质，无缩写歧义

## TypeScript
- 禁止 any
- 完整类型标注
- 使用 strict mode
- 优先 interface over type (public API)

## 错误处理
- 完整覆盖，无静默吞异常
- 使用 Result/Either 模式或 try-catch
- 错误信息要有上下文

## 注释
- 代码自解释，减少注释
- 复杂逻辑写 why，不写 what
- 公共 API 必须 JSDoc/TSDoc
