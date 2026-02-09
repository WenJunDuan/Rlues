# 参考资料索引

## 概述
本目录包含开发过程中的参考资料和标准规范。

## 文件清单

| 文件 | 用途 | 加载时机 |
|:---|:---|:---|
| mcp-tools.md | MCP 工具清单 | 需要调用工具时 |
| frontend-standards.md | 前端开发规范 | 前端开发时 |
| backend-standards.md | 后端开发规范 | 后端开发时 |
| official-skills.md | 官方技能对接 | 集成外部技能时 |

## 使用方式

### 按需加载
```yaml
前端项目: 
  加载 frontend-standards.md

后端项目:
  加载 backend-standards.md

使用 MCP:
  参考 mcp-tools.md

集成外部:
  参考 official-skills.md
```

### 引用方式
在开发过程中引用:
```
参考: references/frontend-standards.md 第3节
```
