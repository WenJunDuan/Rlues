### 1. 通用 JSON 版 (推荐)

#### 适用于 Claude Desktop, Cursor 等大多数客户端

```json
{
  "mcpServers": {
    "mcp-deepwiki": {
      "command": "npx.cmd",
      "args": ["-y", "mcp-deepwiki@latest"]
    },
    "chrome-devtools": {
      "command": "npx.cmd",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    },
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

[mcp_servers.mcp-deepwiki]
type = "stdio"
command = "npx.cmd"
args = ["-y", "mcp-deepwiki@latest"]

[mcp_servers.augment-context-engine]
type = "stdio"
command = "auggie"
args = ["--mcp"]

[mcp_servers.augment-context-engine.env]
AUGMENT_API_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AUGMENT_API_URL = "https://acemcp.heroman.wtf/relay/"

[mcp_servers."cunzhi"]
type = "stdio"
command = "自己的目录\\cunzhi-cli\\寸止.exe"

[mcp_servers.chrome-devtools]
command = "npx.cmd"
args = ["-y", "chrome-devtools-mcp@latest"]

```
