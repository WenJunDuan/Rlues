# Pi

Athena 的 Pi 端分两份，不要混：

| 目录 | 是什么 | 给谁 |
|---|---|---|
| **[plugin/](plugin/)** | `athena-pace` 插件 | 任何人 `pi install`。PACE、`.ai_state` 合同、门禁、核心 prompt |
| **[config/](config/)** | 你的私人配置 | 只给你。模型、第三方包、薄 AGENTS.md、rules |

`.ai_state/` 在**业务项目仓库**里，不在这两份里。

```bash
# 插件（可给别人）
pi install /绝对路径/vibeCoding/pi/plugin

# 私人配置（软链到 ~/.pi/agent，不要链整个目录）
PI=~/.pi/agent
SRC=/绝对路径/vibeCoding/pi/config
mkdir -p "$PI"
for f in AGENTS.md settings.json models.json rules; do
  ln -sfn "$SRC/$f" "$PI/$f"
done
```
