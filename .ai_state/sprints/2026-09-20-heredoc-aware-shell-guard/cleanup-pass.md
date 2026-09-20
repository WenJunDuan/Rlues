---
sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
result: PASS
polish_commit: "a2bba73"
---

# Cleanup Pass — heredoc 感知 shell guard

polish-worker（唯一 writer，主仓串行）五项检查，主 agent 复核后落盘。

| 项 | 结论 |
|---|---|
| 临时代码 | 无发现（命中项均为 fixture 正文） |
| 注释 | 无发现：六项非显然决策全在案且三端逐字一致（白名单文法/正集判据/掩码定序/等长置换/惰性回退/`\r` 有意偏离双写） |
| 冗余 | 1 处已修：CX `mask_body` 逐字符生成器改 `re.sub`，与 CC/Pi 的 `.replace(/[^\n]/g," ")` 三端可比且去热路径逐字节开销；输出逐字节相同 |
| 低效 | 同上一处；`simpleHeredoc` 单遍性核实（一次 regex + 一趟换行行走，无回溯） |
| 过度防御 | 无发现：惰性 try/catch 是安装态信任边界且被 AC4 测试正面钉住；`whole()` 不与 `scalar()` 合参（合参=造出易误设回截断的旋钮，反过度工程反对）；循环上界护栏与显式组判据保留有据 |

主 agent 复核：74/74 绿（任务书 75 为计数偏差，polish 用基线重跑证实）；CC==Pi 双文件字节相等；AC3 基线 pin 未动；stash 栈清洁。行为与消息零变化。
