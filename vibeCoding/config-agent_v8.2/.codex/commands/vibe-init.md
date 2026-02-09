# vibe-init

项目初始化。创建 .ai_state/ 和 .knowledge/ 结构。

## 语法

```
vibe-init
vibe-init --scan
```

## 工具

| 工具 | 用法 |
|:---|:---|
| sou | --scan 时搜索项目结构 |
| deepwiki | --scan 时查询技术栈文档 |
| grep / find | 扫描目录结构和配置文件 |

## 流程

```
1. 检查 .ai_state/ 存在? → 有则提示 vibe-resume
2. 创建 .ai_state/ (从 templates/ai-state/ 复制)
   session.md ← 项目名 + 时间 + Path: 待定 + riper_phase: init
3. 创建 .knowledge/ (如不存在)
4. --scan: 扫描项目
   → find/grep 识别结构
   → sou 搜索核心模块
   → deepwiki 查询框架文档
   → 写入 .knowledge/project/overview.md
   → 写入 .ai_state/conventions.md
5. 建议 .gitignore 添加 .ai_state/ 和 .knowledge/
```
