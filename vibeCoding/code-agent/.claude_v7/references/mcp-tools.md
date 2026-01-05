# MCP 工具参考

## 工具矩阵

| 类别 | 工具 | 用途 | 降级方案 |
|:---|:---|:---|:---|
| **交互** | `寸止` | 用户询问/反馈/确认 | ⛔ 无降级 |
| **记忆** | `memory` | recall/add | 本地Markdown |
| **搜索** | `sou` (augment) | 代码语义搜索 | grep/find |
| **思考** | `sequential-thinking` | 深度推演 | Extended Thinking |
| **需求** | `context7` | 需求分析 | 手动分析 |
| **规划** | `shrimp-task-manager` | WBS任务管理 | Markdown Checklist |
| **角色** | `promptx` | 多角色切换 | 手动声明 |
| **执行** | `codex` | 代码执行 | Claude直接执行 |
| **网络** | `fetch` | HTTP请求 | curl命令 |
| **文档** | `mcp-deepwiki` | 技术文档 | Web搜索 |
| **测试** | `chrome-devtools` | 浏览器调试 | 手动测试 |
| **时间** | `server-time` | 获取时间 | 系统命令 |
| **搜索** | `everything` | 文件搜索 | find命令 |
| **技能** | `skills` | 加载技能 | 内置知识 |

## 优先级规则

### 代码搜索
```
sou (augment) > grep > read_file
```

### 用户交互
```
寸止 (必须) > ⛔禁止直接询问
```

### 记忆管理
```
memory.recall/add > 本地笔记
```

### 任务规划
```
shrimp-task-manager > Markdown Checklist
```

### 角色切换
```
promptx.switch() > 手动声明
```

### 深度思考
```
sequential-thinking > Extended Thinking
```

## 启动协议

每次对话开始必须执行：
```
1. memory.recall(project_path)
2. server-time.get()
3. 评估复杂度 → 选择P.A.C.E.路径
```

## 降级策略

工具缺失不中断流程，使用原生能力降级：

| 工具不可用 | 降级方案 |
|:---|:---|
| memory | 本地Markdown笔记 |
| sou | grep + find |
| shrimp | Markdown Checklist |
| sequential-thinking | Extended Thinking |
| codex (连续2次失败) | Claude直接执行 |
| chrome-devtools | 手动测试指导 |
| mcp-deepwiki | Web搜索 |

## 注意

**寸止无降级方案** — 必须通过寸止与用户交互
