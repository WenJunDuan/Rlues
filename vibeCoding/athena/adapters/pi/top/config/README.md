# config · 私人配置

这是**你的 Pi 配置**，不是插件。插件在 [`../plugin/`](../plugin/)（athena-pace）。

只放：模型、第三方 npm 包、薄 AGENTS.md、`rules/`。

```bash
pi install /绝对路径/vibeCoding/pi-agent/plugin

PI=~/.pi/agent
SRC=/绝对路径/vibeCoding/pi-agent/config
mkdir -p "$PI"
for f in AGENTS.md settings.json models.json rules; do
  ln -sfn "$SRC/$f" "$PI/$f"
done
cp "$SRC/auth.json.example" "$PI/auth.json"  # 仅首次；chmod 600
```

