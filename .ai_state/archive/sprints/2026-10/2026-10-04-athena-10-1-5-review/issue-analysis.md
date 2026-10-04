# 根因与边界

R1–R5：独立 architect Kuhn 在临时仓库复现；详细失败输入与修法见 docs/reports/2026-10-04-athena-10-1-5-review.md。展示命令截断不适合作执行身份；writer 必须绑定收集目标并尊重主仓状态所有权；status 需与 ship 的实际拒绝条件一致。

R6/R7：原插件复用共享提示和 agents，却只替换 SKILLS_DIR；templates 与 CLI 搜索路径仍指向安装器。复用同一 build vars 修正路径，不增加运行时兼容分支。

Codex portable 清单 U-001：三次原生加载 hooks=[]，无 stderr/error，已停止该路径；候选保持原来的默认组件发现形态，待解决后再发布。

R9：独立 reviewer Curie 复现；rebind 扫描预先过滤非 PASS，导致最新失败丢失。仅扩展既有命令表保留较新失败，跳过时要求该最新记录成功且可证明；无新状态机。

第二次复审补充：SSH 的 VM 登记可在仓库外消失，较新记录随之变成 kind=other；已入选身份必须接收此记录。筛 source 后关联身份，单独判断该记录是否为可证明 test/typecheck PASS。
