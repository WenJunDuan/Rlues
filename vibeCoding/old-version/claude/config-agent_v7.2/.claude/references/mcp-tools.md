# MCP 工具参考

## 工具矩阵

| 类别 | 工具 | 用途 | 降级方案 |
|:---|:---|:---|:---|
| **交互** | `寸止` | 用户询问/反馈/确认 | ⛔ 无降级 |
| **记忆** | `memory` | recall/add | .ai_state文件 |
| **搜索** | `sou` (augment) | 代码语义搜索 | grep/find |
| **思考** | `sequential-thinking` | 深度推演 | Extended Thinking |
| **需求** | `context7` | 需求分析 | 手动分析 |
| **角色** | `promptx` | 多角色切换 | 手动声明 |
| **执行** | `codex` | 代码执行 | Claude直接执行 |
| **网络** | `fetch` | HTTP请求 | curl命令 |
| **文档** | `mcp-deepwiki` | 技术文档 | Web搜索 |
| **测试** | `chrome-devtools` | 浏览器调试 | 手动测试 |
| **时间** | `server-time` | 获取时间 | 系统命令 |
| **搜索** | `everything` | 文件搜索 | find命令 |
| **技能** | `skills` | 加载技能 | 内置知识 |

---

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
memory > .ai_state文件 > 本地笔记
```

### 深度思考
```
sequential-thinking > Extended Thinking
```

---

## 启动协议

每次对话开始必须执行：
```
1. 读取 .ai_state/active_context.md
2. memory.recall(project_path)
3. server-time.get()
4. 评估复杂度 → 选择P.A.C.E.路径
```

---

## 降级策略

工具缺失不中断流程，使用替代方案：

| 工具不可用 | 降级方案 |
|:---|:---|
| memory | .ai_state文件 |
| sou | grep + find |
| sequential-thinking | Extended Thinking |
| codex (连续2次失败) | Claude直接执行 |
| chrome-devtools | 手动测试指导 |
| mcp-deepwiki | Web搜索 |

---

## 工具使用最佳实践

### Search (sou/grep)
```markdown
- 先用 sou 理解语义，再用 grep 定位细节
- 禁止一次性 read_file 整个大目录
```

### Edit (codex)
```markdown
- 修改前：必须先读取文件最新内容
- 修改后：读取修改后的片段验证（Double Check）
```

### Memory
```markdown
- 你的会话记忆不可靠
- 将所有重要信息写入 .ai_state/active_context.md
- 文件系统是唯一的真理
```

---

## 注意

**寸止无降级方案** — 必须通过寸止与用户交互，禁止直接询问
