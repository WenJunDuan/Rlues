# 官方技能对接指南

## 概述
本文档说明如何集成 Claude Code 官方技能和第三方 MCP 工具。

## Claude Code 官方技能

### 获取方式
```yaml
来源: Claude Code 插件市场
路径: claude.ai/skills
安装: 下载 SKILL.md 放入对应目录
```

### 支持的官方技能
| 技能 | 用途 | 安装路径 |
|:---|:---|:---|
| docx | Word 文档处理 | skills/docx/ |
| pptx | PPT 演示处理 | skills/pptx/ |
| xlsx | Excel 表格处理 | skills/xlsx/ |
| pdf | PDF 文档处理 | skills/pdf/ |
| frontend-design | 前端设计 | skills/frontend-design/ |

### 安装步骤
```bash
# 1. 从官方下载 SKILL.md
# 2. 创建技能目录
mkdir -p .claude/skills/<skill-name>/

# 3. 放入 SKILL.md
cp downloaded/SKILL.md .claude/skills/<skill-name>/

# 4. 在 orchestrator.yaml 中注册 (可选)
```

## MCP 工具集成

### MCP 概述
```yaml
MCP: Model Context Protocol
作用: 扩展 AI 能力的标准协议
方式: 通过 MCP Server 提供工具
```

### 常用 MCP Server
| Server | 用途 | 获取 |
|:---|:---|:---|
| memory | 知识管理 | 官方内置 |
| sequential-thinking | 深度推理 | 官方内置 |
| filesystem | 文件操作 | github.com/modelcontextprotocol |
| github | Git 操作 | github.com/modelcontextprotocol |
| puppeteer | 浏览器自动化 | github.com/modelcontextprotocol |

### MCP 配置
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-filesystem", "/path/to/workspace"]
    }
  }
}
```

## VibeCoding 集成方式

### 技能集成
```yaml
1. 下载官方 SKILL.md
2. 放入 .claude/skills/<name>/
3. 在 orchestrator.yaml 注册
4. 按需在 workflow 中加载
```

### MCP 集成
```yaml
1. 安装 MCP Server
2. 配置 claude_desktop_config.json
3. 在 references/mcp-tools.md 添加说明
4. 在 workflow 中调用
```

### orchestrator.yaml 配置示例
```yaml
# 注册新技能
skills:
  official:
    - name: docx
      path: skills/docx/SKILL.md
      triggers: ["word", "docx", "文档"]
    - name: pdf
      path: skills/pdf/SKILL.md
      triggers: ["pdf", "PDF"]

# 注册 MCP 工具
mcp_tools:
  custom:
    - name: your-tool
      purpose: "自定义功能"
      server: "your-mcp-server"
```

## 技能开发规范

### SKILL.md 结构
```markdown
# 技能名称

## 概述
[技能描述]

## 能力
[能力列表]

## 触发条件
[何时加载]

## 使用方式
[如何调用]

## 示例
[使用示例]

## 依赖
[所需工具/库]
```

### 最佳实践
```yaml
单一职责: 一个技能做一件事
按需加载: 只在需要时加载
降级方案: 提供备用方法
文档完整: 说明清晰
```

## 常见问题

### Q: 如何知道技能是否加载成功？
```yaml
方法:
  1. 查看 .ai_state/active_context.md 的加载记录
  2. 执行相关功能，观察是否正常
  3. 检查错误日志
```

### Q: MCP 工具调用失败怎么办？
```yaml
检查:
  1. MCP Server 是否运行
  2. 配置是否正确
  3. 网络是否通畅
  
降级:
  参考 references/mcp-tools.md 的降级方案
```

### Q: 如何开发自定义技能？
```yaml
步骤:
  1. 创建 .claude/skills/<name>/ 目录
  2. 编写 SKILL.md
  3. 在 orchestrator.yaml 注册
  4. 测试验证
```

## 资源链接
```yaml
Claude Code 技能: claude.ai/skills
MCP 官方: modelcontextprotocol.io
MCP Servers: github.com/modelcontextprotocol/servers
社区技能: github.com/topics/claude-skills
```
