# Implementation review — S1 single-source-build

独立 reviewer：general-purpose 子 agent（同会话派发，只读；在隔离目录解压源码与 9.9.9 基线，自行运行 build 与 fixture）。

| 轮 | Verdict | 发现 | 处置 |
|---|---|---|---|
| 1 | CONCERNS | P1 `rmSync` 无保护 + VERSION 未校验：空 VERSION 配 `--out vibeCoding` 会清掉冻结的 `claude/`（副本实测）；P2 `--check` 不比权限位；BOM 被吞；畸形标记静默放行；大小写冲突（APFS）；stages.yaml 漏 light-ship/skip 条件、skip_polish 误导、packet 范围与 impl-entry 位置不准；P3 测试强度、参数报错、counts 过期 | VERSION/平台/目录校验；先全量组装与目标校验再写；临时目录 + rename；权限位比较；ignoreBOM；残留/二进制标记失败 + `{{athena:!NAME}}` 转义；NFC 小写冲突键；stages.yaml 按 delivery-gate 重写；测试补 10 条 |
| 2 | **PASS** | P3 目标校验未在首写前完成（半成品输出）；P3 两个 adapter 同 dist_dir 未拒 | 两条均修复并加测试（20/20） |

复核事实：三端构建与 `claude/9.9.9`、`codex/9.9.9`、`pi-agent` 的 `diff -r` 仅差 3 个生成文件；空 VERSION 复现退出 2 且基线无损。

VERDICT: PASS
