### 1. 通用 JSON 版 (推荐)

#### 适用于 Claude Desktop, Cursor 等大多数客户端

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "server-time": {
      "command": "uvx",
      "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    },
    "memory": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "E:\\workspace\\AICode\\server-memory\\memory.json"
      }
    },
    "desktop-commander": {
      "command": "npx.cmd",
      "args": ["-y", "@wonderwhy-er/desktop-commander"],
      "env": {
        "SYSTEMROOT": "C:\\Windows"
      }
    },
    "filesystem": {
      "command": "npx.cmd",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "E:\\workspace\\AICode"
      ]
    },
    "everything": {
      "command": "npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    },
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
    "寸止": {
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

[mcp_servers.memory]
type = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-memory"]
MEMORY_FILE_PATH = '自己的目录\\server-memory\\memory.json'

[mcp_servers.sequential-thinking]
type = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]

[mcp_servers.context7]
type = "stdio"
command = "npx"
args = ["-y", "@upstash/context7-mcp","--api-key", "xxxxxxxxxxxxxxxxxxxxxxxxx"]

[mcp_servers.agentskill-mcp]
type = "stdio"
command = "uvx"
args = ["agentskill-mcp", "--skills-dir", 'C:\\Users\\username\\.claude\\skills']

[mcp_servers.fetch]
type = "stdio"
command = "uvx"
args = ["mcp-server-fetch"]

[mcp_servers.fetch.env]
PYTHONIOENCODING = "utf-8"

[mcp_servers.mcp-deepwiki]
type = "stdio"
command = "npx.cmd"
args = ["-y", "mcp-deepwiki@latest"]

[mcp_servers.mcp-feedback-enhanced]
type = "stdio"
command = "uvx"
args = ["mcp-feedback-enhanced@latest"]
autoApprove = ["interactive_feedback"]
timeout = 1200

[mcp_servers.augment-context-engine]
type = "stdio"
command = "auggie"
args = ["--mcp"]

[mcp_servers.augment-context-engine.env]
AUGMENT_API_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AUGMENT_API_URL = "https://acemcp.heroman.wtf/relay/"

[mcp_servers.desktop-commander]
type = "stdio"
command = 'C:\\Program Files\\nodejs\\npx.cmd'
args = ["-y", "@wonderwhy-er/desktop-commander"]

[mcp_servers.desktop-commander.env]
SYSTEMROOT = 'C:\\Windows'

[mcp_servers.everything]
type = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-everything"]

[mcp_servers."cunzhi"]
type = "stdio"
command = "自己的目录\\cunzhi-cli\\寸止.exe"

[mcp_servers.chrome-devtools]
command = "npx.cmd"
args = ["-y", "chrome-devtools-mcp@latest"]

[mcp_servers.promptx]
command = "npx.cmd"
args = ["-y", "@promptx/mcp-server"]

```
