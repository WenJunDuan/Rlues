```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", ""]
    },
    "sequential-thinking": {
      "command": "npx",
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
    "codex": {
      "command": "npx",
      "args": ["-y", "@zenfun510/codex-mcp-go"],
      "env": {
        "OPENAI_API_KEY": "your-api-key"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "E:/workspace/AICode/server-memory/memory.json"
      }
    },
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    },
    "shrimp-task-manager": {
      "command": "npx",
      "args": ["E:/workspace/AICode/mcp-shrimp-task-manager/dist/index.js"],
      "env": {
        "DATA_DIR": "E:/workspace/AICode/mcp-shrimp-task-manager/data",
        "TEMPLATES_USE": "en",
        "ENABLE_GUI": "true"
      }
    },
    "mcp-deepwiki": {
      "command": "npx",
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
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    },
    "augment-context-engine": {
      "command": "auggie",
      "args": ["--mcp"],
      "env": {
        "AUGMENT_API_TOKEN": "",
        "AUGMENT_API_URL": "https://acemcp.heroman.wtf/relay/"
      }
    },
    "promptx": {
      "command": "npx",
      "args": ["-y", "@promptx/mcp-server"]
    },
    "寸止": {
      "command": "寸止"
    }
  }
}
```
