---
description: "VibeCoding 项目初始化。在项目根目录创建 .ai_state/ 状态管理目录和模板文件。当用户说'初始化 VibeCoding''init''创建状态目录''设置开发环境'时触发。"
name: VibeCoding Init
---

# 项目初始化

## 操作步骤

### 1. 创建 .ai_state/ 目录

在项目根目录下创建以下文件：

**state.json** — 当前阶段和路径
```json
{
  "phase": "idle",
  "path": "",
  "task": "",
  "updated": "",
  "lastSession": "",
  "sessionStatus": "",
  "backlog": []
}
```

**feature_list.json** — 功能/任务清单
```json
{
  "features": [],
  "completed": 0,
  "total": 0
}
```

**progress.json** — 整体进度
```json
{
  "percent": 0,
  "started": "",
  "updated": ""
}
```

**quality.json** — 质量评估结果
```json
{
  "verdict": "",
  "dimensions": {},
  "issues": [],
  "timestamp": ""
}
```

**lessons.md** — 经验教训
```markdown
# 经验教训

<!-- 开发过程中的重要发现、踩坑记录、最佳实践 -->
```

### 2. 探索项目结构

创建完状态文件后：
1. 检测项目类型：
   - package.json → Node.js / 前端
   - Cargo.toml → Rust
   - go.mod → Go
   - pyproject.toml / requirements.txt → Python
   - pom.xml / build.gradle → Java
2. 识别测试框架和测试命令
3. 识别 lint / format 工具

### 3. 输出初始化摘要

```
✅ VibeCoding 初始化完成
- 项目类型: [type]
- 状态目录: .ai_state/ (5 个文件)
- 测试命令: [command] (如检测到)
- 现在可以开始使用 VibeCoding 开发流程
```
