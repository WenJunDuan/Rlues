# VibeCoding Rules

## 代码规范

- 修复 bug 必须同时写回归测试, 不允许裸修复
- 删除代码优于注释代码, 注释掉的代码不允许提交
- 不引入未使用的依赖, 不留 dead code
- 函数超过 50 行 → 拆分, 文件超过 300 行 → 考虑拆分

## Git 规范

- commit message 用 conventional commits 格式
- 一个 commit 做一件事, 不混合功能和重构
- 不 commit generated files (除非 .gitignore 明确排除)

## 安全规范

- 不硬编码 secrets, 用环境变量
- 不信任用户输入, 始终验证和转义
- 依赖更新: `npm audit` 有 high/critical → 必须处理
- PreToolUse hook 自动拦截危险 bash 命令

## .ai_state 规范

- 每个阶段结束必须更新对应文件
- doing.md 实时更新, 不攒到最后
- archive 保留最近 10 次, 超出自动清理
- requirements/ 放需求文档, assets/ 放设计图, 不混用

## 降级规范

- SP 不可用 → 按 riper-7 步骤手动执行, 不跳步
- Plugin 不可用 → AI 原生能力替代, 不报错
- MCP 不可用 (除 cunzhi) → 本地命令替代
- cunzhi 不可用 → 对话确认替代, 不跳过
- PostToolUse hook 失败 → 静默继续, 不阻断写入
