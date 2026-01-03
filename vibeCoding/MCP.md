### 1. 通用 JSON 版 (推荐)

适用于 Claude Desktop, Cursor, Codex 等大多数客户端。

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx.cmd",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", ""]
    },
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
    "mcp-feedback-enhanced": {
      "command": "uvx",
      "args": ["mcp-feedback-enhanced@latest"],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
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
    "skills": {
      "command": "uvx",
      "args": [
        "agentskill-mcp",
        "--skills-dir",
        "C:\\Users\\Mi_Manchi\\.claude\\skills"
      ]
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
    "promptx": {
      "command": "npx.cmd",
      "args": ["-y", "@promptx/mcp-server"]
    },
    "寸止": {
      "command": "E:\\CodeTool\\AICode\\cunzhi-cli\\寸止.exe",
      "args": []
    }
  }
}
```

### 2. TOML 版

适用于部分 Python 工具或特定配置环境。

```ini
[mcp_servers]

[mcp_servers.context7]
command = "npx.cmd"
args = ["-y", "@upstash/context7-mcp", "--api-key", ""]

[mcp_servers.sequential-thinking]
command = "npx.cmd"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]

[mcp_servers.server-time]
command = "uvx"
args = ["mcp-server-time", "--local-timezone=Asia/Shanghai"]

[mcp_servers.fetch]
command = "uvx"
args = ["mcp-server-fetch"]

[mcp_servers.fetch.env]
PYTHONIOENCODING = "utf-8"

[mcp_servers.memory]
command = "npx.cmd"
args = ["-y", "@modelcontextprotocol/server-memory"]

[mcp_servers.memory.env]
MEMORY_FILE_PATH = 'E:\workspace\AICode\server-memory\memory.json'

[mcp_servers.mcp-feedback-enhanced]
command = "uvx"
args = ["mcp-feedback-enhanced@latest"]
timeout = 600
autoApprove = ["interactive_feedback"]

[mcp_servers.desktop-commander]
command = "npx.cmd"
args = ["-y", "@wonderwhy-er/desktop-commander"]

[mcp_servers.desktop-commander.env]
SYSTEMROOT = 'C:\Windows'

[mcp_servers.filesystem]
command = "npx.cmd"
args = ["-y", "@modelcontextprotocol/server-filesystem", 'E:\workspace\AICode']

[mcp_servers.everything]
command = "npx.cmd"
args = ["-y", "@modelcontextprotocol/server-everything"]

[mcp_servers.mcp-deepwiki]
command = "npx.cmd"
args = ["-y", "mcp-deepwiki@latest"]

[mcp_servers.skills]
command = "uvx"
args = ["agentskill-mcp", "--skills-dir", 'C:\Users\Mi_Manchi\.claude\skills']

[mcp_servers.chrome-devtools]
command = "npx.cmd"
args = ["-y", "chrome-devtools-mcp@latest"]

[mcp_servers.augment-context-engine]
command = "auggie"
args = ["--mcp"]

[mcp_servers.augment-context-engine.env]
AUGMENT_API_TOKEN = ""
AUGMENT_API_URL = ""

[mcp_servers.promptx]
command = "npx.cmd"
args = ["-y", "@promptx/mcp-server"]

[mcp_servers."寸止"]
command = 'E:\CodeTool\AICode\cunzhi-cli\寸止.exe'
args = []
```
