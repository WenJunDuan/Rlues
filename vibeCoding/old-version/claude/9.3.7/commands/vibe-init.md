---
effort: low
---
# /vibe-init — 初始化项目环境

> 前置条件: 已运行过 /vibe-install 安装全部插件
> 每个新项目运行一次

## 流程

### 1. 激活 @scaffolder agent

@scaffolder 执行以下初始化:

### 2. 创建 .ai_state/ 目录 + 状态文件
```
.ai_state/
├── state.json          # 总控状态 (path/phase/sprint)
├── feature_list.json   # 验收真值源 (初始为空数组 [])
├── quality.json        # 评分 (初始为空)
├── progress.json       # 跨 session 日志 (初始为空 sessions)
├── design.md           # 技术方案 (模板)
├── plan.md             # 任务列表 (模板)
├── doing.md            # 执行看板 (模板)
└── knowledge.md        # 经验沉淀 (模板)
```

### 3. 生成 init.sh
检测项目类型, 生成对应的启动脚本:
- Node 项目 → `npm install && npm run dev`
- Python 项目 → `pip install && python manage.py runserver`
- 添加端口等待逻辑 + Playwright 基线验证 (如适用)

### 4. 检测项目环境
- 读 package.json / requirements.txt / go.mod 等
- 检测 .git/ 是否存在 (否则 `git init`)
- 检测测试框架 (jest / pytest / vitest 等)

### 5. 已有项目 → 代码地图
```
/gsd:map-codebase
```
GSD 扫描代码结构, 生成代码地图, 帮助后续 R 阶段快速理解

### 6. 输出项目概况
```
📋 VibeCoding 项目初始化完成
━━━━━━━━━━━━━━━
项目: [名称]
类型: [Node/Python/Go/...]
Git: [已初始化/新初始化]
测试: [jest/pytest/...]
.ai_state/: ✅ 已创建
init.sh: ✅ 已生成
━━━━━━━━━━━━━━━
→ 可以开始: /vibe-dev [需求描述]
```
