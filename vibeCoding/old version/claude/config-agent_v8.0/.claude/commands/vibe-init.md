# vibe-init

增强 `/init`，初始化项目 AI 协作环境。

## 执行流程

```
1. /init                          # 调用官方初始化
2. 创建 .ai_state/ 目录结构       # 状态管理
3. 创建 .knowledge/ 目录结构      # 知识库
4. 写入 session.md 初始状态       # 会话锁
5. 检测项目类型 → 写入 conventions.md
```

## .ai_state 初始化

```markdown
# .ai_state/plan.md
> 暂无活跃计划

# .ai_state/todo.md
## 📥 待办
(空)

# .ai_state/doing.md
## 🔄 进行中
(空)

# .ai_state/done.md
## ✅ 已完成
(空)

# .ai_state/archive.md
## 📦 归档
(空)

# .ai_state/decisions.md
## 📐 决策记录
| 日期 | 决策 | 理由 | 状态 |
|:---|:---|:---|:---|

# .ai_state/conventions.md
## 📏 项目约定
(由 vibe-init 自动检测填充)

## 🚫 用户纠正记录
(用户指出的禁止行为记录在此)

# .ai_state/session.md
## 会话状态
- locked: false
- last_updated: {{timestamp}}
- current_task: null
- pace_path: null
```

## .knowledge 初始化

```
.knowledge/
├── index.md          # 知识索引
├── project/          # 项目文档
├── standards/        # 开发规范
├── company/          # 团队约定
└── tech/             # 技术栈参考
```

## 自动检测

vibe-init 会扫描项目根目录，自动写入 conventions.md：

- `package.json` → Node.js 项目，记录框架/lint 配置
- `tsconfig.json` → TypeScript 项目，记录 strict 模式
- `.eslintrc` → ESLint 规则
- `pyproject.toml` → Python 项目
- `go.mod` → Go 项目
- `.editorconfig` → 编辑器配置

## 寸止

初始化完成后调用 cunzhi `[INIT_DONE]`，汇报检测结果。
