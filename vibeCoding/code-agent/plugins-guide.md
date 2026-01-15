# 插件集成指南

## 概述
VibeCoding 支持通过 MCP 工具和官方 Skills 扩展能力。本指南介绍如何集成和使用这些插件。

## 插件类型

### 1. MCP 工具
```yaml
定义: Model Context Protocol 工具
安装: 通过 claude_desktop_config.json 配置
调用: 在工作流中通过 MCP 协议调用
```

### 2. 官方 Skills
```yaml
定义: Claude Code 官方技能
安装: 下载 SKILL.md 到 skills/ 目录
调用: 按需加载执行
```

### 3. 自定义 Skills
```yaml
定义: 用户自定义技能
创建: 编写 SKILL.md 文件
调用: 在 orchestrator.yaml 注册后使用
```

## MCP 工具集成

### 配置文件
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
// %APPDATA%/Claude/claude_desktop_config.json (Windows)

{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-filesystem", "/path/to/workspace"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

### 常用 MCP 工具

#### memory
```yaml
用途: 知识持久化
安装: 内置
配置: 无需额外配置
```

#### sequential-thinking
```yaml
用途: 深度推理
安装: 内置
配置: 无需额外配置
```

#### filesystem
```yaml
用途: 文件系统操作
安装: npm install -g @anthropic/mcp-filesystem
配置: 指定工作目录
```

#### github
```yaml
用途: Git 操作
安装: npm install -g @anthropic/mcp-github
配置: 需要 GITHUB_TOKEN
```

#### puppeteer / playwright
```yaml
用途: 浏览器自动化
安装: npm install -g @anthropic/mcp-puppeteer
配置: 可选 headless 模式
```

### 在 VibeCoding 中使用

#### 注册到 orchestrator.yaml
```yaml
mcp_tools:
  custom:
    - name: github
      purpose: "Git 操作"
      server: "github"
    - name: puppeteer
      purpose: "浏览器测试"
      server: "puppeteer"
```

#### 在工作流中调用
```markdown
# 在 Execute 阶段

**MCP 增强**:
\`\`\`yaml
代码提交: github MCP
  调用: github_commit({ message: "feat: add login" })

E2E测试: puppeteer MCP
  调用: puppeteer_screenshot({ url: "http://localhost:3000" })
\`\`\`
```

## 官方 Skills 集成

### 获取官方 Skills
```yaml
来源:
  - Claude Code 插件市场
  - Anthropic 官方仓库
  - 社区贡献

格式:
  - SKILL.md 文件
  - 可能包含辅助脚本
```

### 安装步骤
```bash
# 1. 创建技能目录
mkdir -p .claude/skills/<skill-name>/

# 2. 下载或复制 SKILL.md
cp /path/to/SKILL.md .claude/skills/<skill-name>/

# 3. (可选) 在 orchestrator.yaml 注册
```

### 常用官方 Skills

#### docx
```yaml
用途: Word 文档处理
能力: 创建、编辑、转换 .docx 文件
安装路径: skills/docx/SKILL.md
```

#### pptx
```yaml
用途: PPT 演示处理
能力: 创建、编辑幻灯片
安装路径: skills/pptx/SKILL.md
```

#### xlsx
```yaml
用途: Excel 表格处理
能力: 数据分析、公式计算
安装路径: skills/xlsx/SKILL.md
```

#### pdf
```yaml
用途: PDF 文档处理
能力: 读取、创建、转换 PDF
安装路径: skills/pdf/SKILL.md
```

## 自定义 Skills 开发

### SKILL.md 结构
```markdown
# 技能名称

## 概述
[技能描述]

## 能力
[能力列表]

## 触发条件
[何时加载此技能]

## 使用方式
[如何调用]

## 示例
[使用示例]

## 依赖
[所需的工具或库]

## 最佳实践
[使用建议]
```

### 示例: 自定义代码审查技能
```markdown
# Code Review Skill

## 概述
自动化代码审查，检查常见问题。

## 能力
- 检查代码风格
- 识别潜在 bug
- 建议优化点

## 触发条件
- Review 阶段
- 用户请求代码审查

## 使用方式
\`\`\`javascript
code_review({
  files: ["src/auth.ts"],
  rules: ["style", "security", "performance"]
})
\`\`\`

## 检查规则
### 风格
- 命名规范
- 代码格式

### 安全
- 输入验证
- SQL 注入

### 性能
- N+1 查询
- 内存泄漏
```

### 注册自定义 Skill
```yaml
# orchestrator.yaml

skills:
  custom:
    - name: code-review
      path: skills/code-review/SKILL.md
      triggers: ["review", "审查", "检查代码"]
```

## 最佳实践

### 插件选择
```yaml
优先使用:
  1. 内置 MCP 工具 (memory, sequential-thinking)
  2. 官方 Skills
  3. 社区推荐插件

避免:
  - 功能重复的插件
  - 未维护的插件
  - 权限过大的插件
```

### 性能考虑
```yaml
- 按需加载，避免预加载所有插件
- MCP 工具有网络开销，合理使用
- 大型 Skills 考虑拆分
```

### 安全考虑
```yaml
- 审查插件权限
- 敏感操作需要确认
- 定期更新插件版本
```

## 故障排除

### MCP 工具无法连接
```yaml
检查:
  1. MCP Server 是否运行
  2. 配置文件路径是否正确
  3. 端口是否被占用
  4. 环境变量是否设置
```

### Skill 加载失败
```yaml
检查:
  1. SKILL.md 格式是否正确
  2. 路径是否正确
  3. 依赖是否满足
```

### 工具调用超时
```yaml
解决:
  1. 检查网络连接
  2. 增加超时时间
  3. 使用降级方案
```

## 资源链接

- [MCP 官方文档](https://modelcontextprotocol.io)
- [MCP Servers 仓库](https://github.com/modelcontextprotocol/servers)
- [Claude Code Skills](https://claude.ai/skills)
- [社区插件列表](https://github.com/topics/claude-skills)
