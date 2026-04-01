### 1. 通用 JSON 版 (推荐)

#### 适用于 Claude Desktop, Cursor 等大多数客户端

```json
{
  "mcpServers": {
    "augment-context-engine": {
      "command": "auggie",
      "args": ["--mcp"],
      "env": {
        "AUGMENT_API_TOKEN": "",
        "AUGMENT_API_URL": ""
      }
    },
    "cunzhi": {
      "command": "E:\\CodeTool\\AICode\\cunzhi-cli\\寸止.exe",
      "args": []
    }
  }
}
```

### 2. TOML 版

#### 适用于 codex。

```toml

[mcp_servers]

[mcp_servers."cunzhi"]
type = "stdio"
command = "寸止"

[mcp_servers.augment-context-engine]
type = "stdio"
command = "npx"
args = ["ace-tool-rs", "--base-url", "https://acemcp.heroman.wtf/relay/", "--token", ""]

```
