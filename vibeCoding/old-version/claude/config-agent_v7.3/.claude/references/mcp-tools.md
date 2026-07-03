# MCP 工具参考

## 工具矩阵

| 类别 | 工具 | 用途 | 降级方案 |
|:---|:---|:---|:---|
| **交互** | `寸止` | 用户交互 | ⛔ 无降级 |
| **记忆** | `memory` | recall/add | .ai_state文件 |
| **搜索** | `sou` (augment) | 代码搜索 | grep/find |
| **思考** | `sequential-thinking` | 深度推理 | Extended Thinking |
| **角色** | `promptx` | 多角色切换 | 手动声明 |
| **执行** | `codex` | AI代码执行 | Claude直接执行 |
| **文档** | `mcp-deepwiki` | 技术文档 | Web搜索 |

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

### 执行技能
```
codex/gemini (指定) > Claude原生 (默认)
```

---

## 启动协议

```
1. 读取 project_document/.ai_state/active_context.md
2. memory.recall(project_path)
3. 评估复杂度 → 选择P.A.C.E.路径
```

---

## 降级策略

| 工具不可用 | 降级方案 |
|:---|:---|
| memory | .ai_state文件 |
| sou | grep + find |
| codex | Claude直接执行 |

---

## 注意

**寸止无降级方案** — 必须通过寸止与用户交互
