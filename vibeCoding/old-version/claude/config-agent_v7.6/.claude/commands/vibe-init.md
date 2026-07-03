# /vibe-init - 初始化项目

---

## 作用

在项目根目录创建 `.ai_state/` 目录和必要的状态文件。

---

## 执行步骤

```bash
# 1. 创建目录
mkdir -p .ai_state

# 2. 创建 active_context.md
cat > .ai_state/active_context.md << 'EOF'
# 当前上下文

## 任务
(无)

## TODO
(无)

---
更新时间: [时间戳]
EOF

# 3. 创建 kanban.md
cat > .ai_state/kanban.md << 'EOF'
# 📋 项目看板

## 📊 整体进度
░░░░░░░░░░░░░░░░░░░░ 0%

## 📥 TODO (待办)
(空)

## 🔄 DOING (进行中)
(空)

## ✅ DONE (已完成)
(空)

---
更新时间: [时间戳]
EOF

# 4. 创建 conventions.md
cat > .ai_state/conventions.md << 'EOF'
# 项目约定

## 命名规范
- 文件: kebab-case
- 变量: camelCase
- 类型: PascalCase

## 代码风格
- 函数 < 50 行
- 嵌套 < 3 层

---
更新时间: [时间戳]
EOF

# 5. 创建 decisions.md
cat > .ai_state/decisions.md << 'EOF'
# 技术决策记录

| 日期 | 决策 | 理由 |
|:---|:---|:---|

---
更新时间: [时间戳]
EOF
```

---

## 输出

```
✅ 项目已初始化

创建的文件：
- .ai_state/active_context.md
- .ai_state/kanban.md
- .ai_state/conventions.md
- .ai_state/decisions.md

下一步：使用 /vibe-plan 或 /vibe-code 开始工作
```
