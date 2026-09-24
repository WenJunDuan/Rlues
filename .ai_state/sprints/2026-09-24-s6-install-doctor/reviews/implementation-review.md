# Implementation review — S6 install / rollback / doctor

独立 reviewer：general-purpose 子 agent，临时 HOME 对抗探针（未触碰真实 HOME）。

| 轮 | 结论 | 要点 | 处置 |
|---|---|---|---|
| r1 | REWORK | P1：非标准写法的 `[shell_environment_policy.set]` 被追加第二张表→config.toml 失效；安装中途失败自动还原会抛错留半装；settings.json 为符号链接时被替换成普通文件。P2：用户 hook 按 9.9.9 文件名子串误删；回滚覆盖安装后用户改动；退役目录回滚失败；doctor 看不见 hook 被删；新装 config.toml 版本号仍是 9.9.9 | 只编辑标准表头，其他写法不动并提示；预检（HOME 外路径、文件/目录冲突、manifest 路径）后才写；写穿符号链接；逐项容错还原、after-install/ 留存用户改动；目录用 cpSync 还原；installed.json 记 hook 命令、doctor 校验；hook 匹配限定 ~/.claude|~/.codex/hooks |
| r2 | CONCERNS | P2：中断的重装会被旧 installed.json 盖过；还原出错仍标 rolled_back 无法重试；单引号 TOML 键；P3：tmp 文件残留、doctor 看不出 TOML 重复表、profiles 下同名键误判 | pending 取最新未回滚记录；仅干净还原才关闭记录；`["']?`；tmp 入记录；doctor 查重复表头；其他表头不计入 |

终态：r2 发现项全部修复并加回归（test_install_regressions.py 9 条，含中断重装）。

VERDICT: PASS
