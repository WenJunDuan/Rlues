# Pi

Athena 的 Pi 端分两份，不要混：

| 目录 | 是什么 | 给谁 |
|---|---|---|
| **[plugin/](plugin/)** | `athena-pace` 插件 | 任何人 `pi install`。PACE、`.ai_state` 合同、门禁、核心 prompt |
| **[config/](config/)** | 你的私人配置 | 只给你。模型、第三方包、薄 AGENTS.md、rules |

`.ai_state/` 在**业务项目仓库**里，不在这两份里。

Pi 版本：≥ 0.87（硬 Stop 需要 `agent_before_settle`）；按 1.0.2 源码核对。更低版本能装，Stop 退回 followUp 软提示。

```bash
# 插件（可给别人）。本地路径或 git 源二选一
pi install /绝对路径/vibeCoding/dist/pi/<版本>/plugin
pi install git:<host>/<owner>/<repo>@<tag>      # 仓库根须是 plugin 包（package.json#pi）；待本机验证

# 私人配置（软链到 ~/.pi/agent，不要链整个目录）
PI=~/.pi/agent
SRC=/绝对路径/vibeCoding/dist/pi/<版本>/config
mkdir -p "$PI"
for f in AGENTS.md settings.json models.json rules; do
  ln -sfn "$SRC/$f" "$PI/$f"
done
```

硬 Stop、codemode、待本机验证清单：见 [plugin/README.md](plugin/README.md)。
