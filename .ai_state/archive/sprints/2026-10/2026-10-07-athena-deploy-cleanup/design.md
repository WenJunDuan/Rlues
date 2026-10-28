---
sprint: "2026-10-07-athena-deploy-cleanup"
path: "Quick"
created: "2026-10-07"
req: "system-deployment-maintenance"
roadmap: ""
item: ""
base_commit: "034058a"
review_ignore: []
---

# Design — 2026-10-07-athena-deploy-cleanup

## 背景

用户要求核对并更新 CC/CX 系统部署、保留会话历史、清除无效缓存、删除 pre tag。仓库及 origin 最新发布为 10.1.5（034058a）；系统 doctor 报 10.1.0。分诊 Quick：同一部署维护任务，无源码行为改动。

## 方案

从当前源码构建到临时目录，使用官方 install CLI 合并平台配置并创建回滚备份。安装前记录会话文件摘要，验证历史文件旧内容未变、数据库原文件仍在。只删除有证据可重建且未被进程使用的临时克隆、遗留临时文件与 Finder/Python 缓存。清理退役技能时仅处理 Athena 管理的重复/退役文件，保留用户自有技能。删除明确唯一的 pre-athena-10.1-state 本地及 origin 标签，保留正式版本标签。

## 验收标准

- AC1: 系统 CC/CX 安装记录为 10.1.5，托管文件与本次源码构建一致，doctor 无漂移，CLI 可从登录 shell 调用。
- AC2: 安装计划与清理清单不触及会话/历史/数据库；既有会话文件旧内容摘要一致，数据库文件原 inode 保留，用户配置与 hook 保留。
- AC3: 清理清单内确认无效且未使用的缓存被移除，最新回滚备份保留，报告删除数量与体积。
- AC4: 本地及 origin 的 pre-athena-10.1-state 均不存在，正式 v10.1.0/v10.1.5 标签保留。

## 允许写集

`.ai_state` 本任务记录；`~/.athena`、CC/CX 托管配置/规则/角色/技能；已审核缓存清单；CLI PATH 配置；指定本地及远程 tag。系统目录写入经沙箱权限批准执行。

## 不做

不删除会话、项目记忆、附件、认证、有效插件缓存、工作区或正在使用的临时目录；不修改源码，不删除正式标签。
