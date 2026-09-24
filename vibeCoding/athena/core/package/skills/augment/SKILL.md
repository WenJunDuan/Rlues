---
name: augment-context-engine
description: 用自然语言在项目代码里语义检索（有没有已有实现、改动影响哪些调用方）时用；精确字符串用 rg。
---

# augment — 项目代码语义检索

何时用：design 查「已有类似实现吗」「改这个影响谁」；review 查「删掉的 export 还有引用吗」。找确定字符串用 `rg`。

## 步骤

1. 用 augment-context-engine MCP 的 `search_context`，写具体的自然语言查询（如「JWT 校验的已有实现」）。
2. 对返回的路径用 `rg` / 读文件核实；语义检索结果不直接当事实。
3. 结论（复用哪段代码、影响哪些调用方）写进 design.md。

## 约束

- MCP 设 `approval_mode = "approve"`：远程服务会收到代码片段，调用前需用户同意。
- token 只放用户本机配置，模板里用 `<YOUR_ACE_TOKEN>` 占位。
- 没有 token 或服务不可用：降级 `rg`，不阻塞流程。
- 子 agent 调研时在任务里写明问题与允许的 MCP 工具；不把 agent 名当 shell 命令。

完成条件：结论已用 rg 或读文件核实，并写进 design。
