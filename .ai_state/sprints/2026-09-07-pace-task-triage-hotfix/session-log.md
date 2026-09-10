# 自然语言任务路由 Hotfix（9.9.9）

## 2026-09-08 规则同步追加

- 用户要求将Claude现场裁定同步回9.9.9仓库和CX安装态：ff合并到main并复验通过后立即删除worktree与临时分支，返工重建；push/PR仍遵循授权与门禁。
- 作为已授权Hotfix规则纠偏延续；候选Quick仅机械同步，采用当前Hotfix有界文档修订，conf=1.0。无代码/权限配置变更，无实际worktree或分支删除，不新增自动清理hook。
- CC两个源码文件与安装态逐字同步；CX保留原生派工差异，只同步清理语义，并更新 `.agents` 与 `.codex` 两份安装文件。
- 已核对并删除CC两个 `*.md.bak-20260907-wt`，其内容与仓库修改前版本完全相同，可从Git恢复。CX四份安装前备份位于 `/Users/mi_manchi/.athena/backups/athena-9.9.9-worktree-muBM1M`。
- 验证：两端pace的quick_validate通过，6/6源码/安装文件对照一致，两个指定CC备份已不存在，git diff --check通过。本次为纯文档规则修订，不制造行为测试；本轮未要求commit/push，保留工作区改动。

目标：一句话/一段话任务自动识别检查/诊断/实现与实际风险；显式Hotfix立即执行，独立Quick诊断不消费旧System门禁。用户给出的OpenList服务器请求是分诊样例，本轮没有连接服务器。
允许范围：CC/CX athena-dev与PACE入口、根提示、CX状态修复门禁及相关回归；系统目录同步后提交推送。父任务恢复入口：../2026-09-06-athena-9-9-9/session-log.md 的“独立路由Hotfix插入恢复点”；父System验收保持未完成。
分诊：沿本次已授权9.9.9 Hotfix继续；候选Quick仅文档路径不能覆盖CX门禁实测缺陷，采用Hotfix有界修复，conf=1.0。所有产出仅反映结论、证据，不记录原始推理。
完成条件：两端状态修复允许而源码/Stop仍受检；独立Quick/Hotfix可结束且不冒充父System通过；OpenList自然语言样例明确安排只读检查；发行与安装一致，校验通过并推送。

## 已证实根因与修复

- athena-dev/playbook无条件先消费旧next_action，CX显式Hotfix还指向plan；已统一语义分诊和Hotfix直达impl。
- 旧playbook使用未定义的shell伪命令、强制复制checklist/route-note；已改成现有索引/日志切换合同和按需文书。
- 只改route_history不改实际path/stage/slug导致旧门禁继续生效；独立执行任务现在记录真实新范围，旧任务恢复字段保留。
- CX impl分支拦截.ai_state修复：双端回归先RED再GREEN；源码写与Stop仍block。独立Quick/Hotfix与父System的隔离回归通过。
- 独立行为评估由真实target /root/triage_behavior_check 完成；初评发现旧5步引用、模糊判定时序、Bugfix单文件边界3处漂移；复核确认独立Quick接管索引可执行，补充指出Quick表格和通用plan设计义务2处冲突。以上5处均已在两端修正。

## 部署与验证

- `python3 -B vibeCoding/scripts/validate-athena-9.9.9.py`：exit 0，package_checks_pass=60 fail=0；这是当前Hotfix包校验，不代表父System整体验收。
- 新增双端回归覆盖：impl状态修复允许，但源码写与Stop仍受检；独立Quick/Hotfix结束不满足旧System合同。测试子进程禁止写字节码，生成缓存已移到备份目录。
- 本机15个目标逐文件备份后同步：CC根提示与4个skill文件；CX根提示、4个canonical skill文件及4个legacy镜像、delivery-gate.py。读回15/15字节相同；未更改用户模型、effort、账号或agent配置。
- 备份及清单：`/Users/mi_manchi/.athena/backups/athena-9.9.9-triage-njDGcQ/manifest.json`。legacy playbook原有平台适配差异均在被新任务切换合同替换的段落，备份保留原文。
- 当前Hotfix进入ship，父System保持未完成；提交和远端结果以本目录git历史为准，不自动恢复执行旧任务。
- 安装态CC/CX delivery-gate以本仓库真实Hotfix/ship索引执行Stop：两端exit 0，无block输出；未设置绕过门禁环境变量。`git diff --check`通过。
