# /vibe-code - 执行编码

---

## 作用

自动评估复杂度，选择路径，执行完整 RIPER 流程。

---

## 语法

```bash
/vibe-code [描述] [--engine=xxx] [--path=X]
```

---

## 执行流程

```
1. 检查 session.lock
   ├── 存在 → 提示恢复未完成工作流
   └── 不存在 → 继续

2. 复杂度评估
   ├── 文件数量
   ├── 代码行数
   ├── 预估时间
   ├── 架构影响
   └── 依赖数量

3. 选择路径
   ├── ≤3 → Path A（加载 workflows/path-a.md）
   ├── 4-6 → Path B（加载 workflows/path-b.md）
   └── ≥7 → Path C（加载 workflows/path-c.md）

4. 执行 RIPER
   ├── R1: skills/research.md
   ├── I:  skills/innovate.md（B/C）
   ├── P:  skills/plan.md
   ├── E:  skills/execute.md
   └── R2: skills/review.md

5. 寸止确认
   └── 调用 cunzhi / mcp-feedback
```

---

## 参数

| 参数 | 说明 | 示例 |
|:---|:---|:---|
| `--engine` | 指定执行引擎 | `--engine=codex` |
| `--path` | 强制路径 | `--path=C` |
| `--strict` | 严格模式 | `--strict` |
| `--tdd` | TDD 模式 | `--tdd` |

---

## 示例

```bash
# 自动评估
/vibe-code 实现用户登录功能

# 强制 Path C
/vibe-code --path=C 重构认证系统

# 使用 Codex
/vibe-code --engine=codex 修复登录Bug
```
