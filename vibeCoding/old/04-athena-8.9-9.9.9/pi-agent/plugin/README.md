# plugin · athena-pace

这是**插件**，不是私人配置。私人配置在 [`../config/`](../config/)。

Pi package：PACE + `.ai_state` 合同 + 门禁 + 核心 prompt。  
`.ai_state/` 在**每个项目仓库**，本包不携带 sprint。

```bash
pi install /绝对路径/vibeCoding/pi-agent/plugin
```

## 装进去什么

| 层 | 内容 |
|---|---|
| extensions | `athena-gates`（bash/write 门禁，`agent_end` followUp）· `athena-lifecycle`（面包屑、compact、铁律短注入） |
| skills | pace · athena-dev · athena-init · athena-status · brainstorm · roadmap · compound · athena-review · polish · athena-runtime-verify · athena-issue · architect-doc |
| prompts | `/generator` `/reviewer` `/architect` `/polish-worker` |
| core/IRON.md | 常驻短规则（lifecycle 追加进 system prompt） |

不含：你的模型/API、fff/btw 等第三方包、quantum 业务 skill。那些放个人 `settings.json`。

## 新项目

git 仓库里 `/athena-init` → 建 `.ai_state/`。已有不覆盖。

## 限制

Pi Stop 不能硬拦交付。红区无 `isolation: worktree`，用 git worktree。门禁逻辑目前仍调包内 `extensions/cc-core/*.cjs`（实现细节，不是给用户的第二套 hook）。
