---
description: VibeCoding指令索引 v7.5
---

# VibeCoding Commands

## 设计原则

1. **前缀隔离**: 所有指令使用 `vibe-` 前缀
2. **工作流模式**: 进入工作流后锁定，直到完成或暂停
3. **生命周期**: 每个指令有完整的生命周期钩子

---

## 🚀 工作流指令

| 指令 | 简写 | 描述 | 创建锁 |
|:---|:---|:---|:---|
| `/vibe-plan` | `/vp` | 深度规划模式 | ✅ |
| `/vibe-design` | `/vd` | 架构设计模式 | ✅ |
| `/vibe-code` | `/vc` | 编码执行模式 | ✅ |
| `/vibe-review` | `/vr` | 代码审查模式 | ✅ |

### 参数

```bash
--engine=codex    # 指定 Codex 执行
--engine=gemini   # 指定 Gemini 执行
--tdd             # TDD 模式
--path=C          # 强制 Path C
--strict          # 严格模式
```

---

## 🎮 控制指令

| 指令 | 描述 | 影响锁 |
|:---|:---|:---|
| `/vibe-state` | 查看当前状态 | ❌ |
| `/vibe-pause` | **暂停工作流** | 释放锁 |
| `/vibe-resume` | **恢复工作流** | 重新锁定 |
| `/vibe-abort` | **终止工作流** | 释放锁 |
| `/vibe-init` | 初始化项目 | ❌ |

---

## 🔒 工作流锁定

### 进入工作流

```
/vibe-code → 创建 workflow.lock → 锁定模式
```

### 解锁条件

- ✅ 所有TODO完成 + 寸止确认
- ⏸️ `/vibe-pause`
- ⛔ `/vibe-abort`

### 锁定期间

- 不能变成普通对话
- 必须保持工作流模式
- 断开会话后恢复时继续工作流

---

## 📋 指令生命周期

```
/vibe-xxx
    │
    ▼
onInit() ─────────▶ 创建锁，初始化状态
    │
    ▼
onPhaseEnter() ───▶ 进入新阶段
    │
    ▼
onTaskStart() ────▶ 任务开始，更新kanban
    │
    ▼
onTaskComplete() ─▶ 任务完成，更新kanban
    │
    ▼
onBeforeComplete()▶ 生成报告，调用寸止
    │
    ▼
onComplete() ─────▶ 释放锁，归档状态
```

---

## 🔄 中断恢复

### 暂停

```
/vibe-pause
    │
    ▼
onPause() ────▶ 保存断点到 checkpoint.md
    │
    ▼
释放锁 ───────▶ 可以进行其他对话
```

### 恢复

```
/vibe-resume
    │
    ▼
onResume() ───▶ 加载 checkpoint.md
    │
    ▼
重新锁定 ─────▶ 继续执行
```

---

## 📂 官方 Plugins

官方 plugins 从 GitHub 复制到此目录：

```bash
git clone https://github.com/anthropics/claude-code.git temp
cp temp/.claude/commands/code-review.md .claude/commands/
rm -rf temp
```

详见 `plugins-guide.md`

---

## 🛑 寸止点

| Token | 触发条件 |
|:---|:---|
| `[PLAN_READY]` | TODO生成完成 |
| `[DESIGN_FREEZE]` | 架构定义完成 |
| `[PHASE_DONE]` | Phase完成 |
| `[TASK_DONE]` | 全部TODO完成 |
| `[VERIFICATION_FAILED]` | 验证失败3次 |

---

**版本**: v7.5 | **模式**: 工作流锁定 | **生命周期**: 完整钩子
