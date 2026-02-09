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
1. 检查是否已有 .ai_state/
   已有 → 提示 vibe-resume
   没有 → 继续

2. 创建 .ai_state/ (从 templates/ai-state/ 复制)
   session.md  ← 项目名 + 当前时间 + Path: 待定 + riper_phase: init
   plan.md     ← 空
   todo.md     ← 空
   doing.md    ← 空
   done.md     ← 空
   conventions.md ← 空

3. 创建 .knowledge/ (如果不存在)
   index.md
   experience/

4. --scan: 扫描项目
   → find / grep: 识别目录结构、入口文件、配置文件
   → sou.search("main entry") 搜索核心模块
   → deepwiki: 查询检测到的框架文档
   → 写入 .knowledge/project/overview.md:
     语言/框架/目录结构/入口文件/依赖
   → 写入 .ai_state/conventions.md:
     检测到的编码风格 (缩进/引号/分号等)

5. 读 .gitignore，建议添加 .ai_state/ 和 .knowledge/
```
