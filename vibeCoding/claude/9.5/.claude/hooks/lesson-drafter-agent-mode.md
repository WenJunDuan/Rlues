# lesson-drafter — 双轨配置说明 (v9.5)

VibeCoding 的 lesson-drafter 提供两个版本, 默认用 cjs (省钱), 可选用 agent (智能):

## 默认: cjs 版本 (settings.json 现有注册)

`~/.claude/hooks/lesson-drafter.cjs` — 用正则识别失败模式, 起草 ~/.claude/lessons/draft-*.md。

优点: 零成本、零延迟、确定性。
缺点: 只识别预定义的失败模式 (permission denied / command not found 等).

## 可选: agent 版本 (用 Haiku 智能识别)

利用 v2.1.116+ 的 `type: "agent"` hook, 让 LLM 自己判断是否值得起草。

优点: 能识别新颖错误模式 (例如某 SDK 的非标准报错).
缺点: 每次 PostToolUse 跑一次 Haiku (~$0.0003/次, 长 session 累积).

### 如何启用 agent 版本

编辑 `~/.claude/settings.json`, 替换 PostToolUse 段下的 lesson-drafter 注册:

```jsonc
// 原 cjs 注册 (默认):
{
  "type": "command",
  "command": "test -f \"$HOME/.claude/hooks/lesson-drafter.cjs\" && node \"$HOME/.claude/hooks/lesson-drafter.cjs\" || true",
  "async": true
}

// 改成 agent 版本:
{
  "type": "agent",
  "prompt": "看本次 tool_input 和 tool_response. 如果含错误模式 (permission denied, command not found, syntax error 等), 起草 ~/.claude/lessons/draft-{slug}.md 包含: 触发场景 + 完整输出 + 推测根因. 不写就什么都不做. 写盘前必须脱敏 (token/secret).",
  "model": "claude-haiku-4-5",
  "async": true,
  "timeout": 30
}
```

### 何时选 agent 版本

- 团队/企业开发, 异常模式多样, 需要智能识别
- 不在乎每月 ~几美元的 Haiku 费用
- 想看 lesson 质量 (agent 版本起草的 draft 含上下文推理, cjs 只是模板填空)

### 何时坚持 cjs 版本

- 个人开发, 控制成本
- 失败模式相对固定 (主要是 permission/network 类)
- 不想引入额外 LLM 调用的不确定性

### 切换回 cjs 版本

把 settings.json 里 PostToolUse 的 lesson-drafter 块改回 cjs 注册即可。

## 安全保证一致

不管 cjs 还是 agent 版本, 都遵守 `_redact.cjs` 的脱敏规则 (token/secret/JWT/SSH-key)。agent 版本的 prompt 里也明示了"写盘前必须脱敏"。
