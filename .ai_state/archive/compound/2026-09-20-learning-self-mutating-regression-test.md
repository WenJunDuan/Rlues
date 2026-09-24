---
type: learning
date: 2026-09-20
sprint: 2026-09-20-evidence-pipeline-integrity
---

# 自我变异的回归测试会留下持久故障

## 事实

`test_ac5_…` 要验证「缺了 `_shell-lex` 时 delivery-gate 仍然拦截」。第一版实现把**已发布包里**的 `_shell-lex.cjs` / `_shell_lex.py` 改名成 `.hidden`，`finally` 再改回来。

两个问题：

1. 运行被强杀、崩溃或机器重启，发行包就缺了 lexer。而 `setup-athena.py` 的 `REQUIRED_ASSETS` 并不列这个新模块，`managed_complete()` 仍判该 home 完整，修复路径永不触发；此后所有验证静默记 `unknown`。测试给自己造了一个检测不到的持久故障。
2. 守卫写成 `if path.exists(): rename(...)`。lexer 若已缺失，测试会**空跑并通过**——它要防的那条路径根本没被执行。

## 改法

把 hook 目录 `copytree` 到临时目录，从**副本**里删；断言针对副本跑。守卫用 `unlink()` 而非 `if exists()`：目标本该存在，不存在就该抛错，而不是让回归悄悄降级成空操作。

实测代价：每次套件运行多复制约 700 KB，总耗时不变（18.3s 前后一致）。

## 判据

一个回归测试如果要模拟「某文件缺失 / 某依赖损坏」，先问：这次运行被 `kill -9` 之后，仓库还能用吗？答案是否，就别改动真实文件。

另一条推论：**守卫不能让断言变成可跳过的**。`if exists()` 型守卫在「前提不成立」时静默放过，正好掩盖了测试存在的理由。前提不成立应当是失败，不是通过。

相关：[[2026-07-28-learning-reserved-ac-labels-silent-exemption]]
