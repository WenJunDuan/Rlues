# Implementation review — S0 gate-hotfix-9-9-9-p1

独立 reviewer：general-purpose 子 agent（同会话派发、只读，逐轮在隔离 fixture 上实跑 CC/CX 两端）。输入：design.md + 完整 diff（每轮刷新）。

| 轮 | Verdict | 发现 | 处置 |
|---|---|---|---|
| 1 | FAIL | P0 `GIT_DIR=… git -C /empty push` 环境变量重定向绕过推送门禁（实测推送成功）；P1 测试未覆盖该向量；P2 CC detector 路径解析与 CX 不对称；P3 Quick 豁免范围 | 命令文本含 `GIT_DIR` 类变量即回落 cwd；补测试；CC 按 payload cwd 解析；P3 按设计保留 |
| 2 | CONCERNS | P2 独立 clone 按自身 stage 判（设计性放宽）；P3 变量表维护 | 不接受放宽：新增 sameProject（共享远端 / 目的地 / 本地远端） |
| 3 | REWORK | P1 CC 本地远端按字面、CX 按真实路径比较 → 软链 / macOS `/var` 拼写在 CC 放行；P2 scp 前导斜杠、`file://`；P2 insteadOf 未展开 | CC realpath；`(?!//)` + file:// 映射；`remote get-url --all/--push --all` + `ls-remote --get-url` |
| 4 | CONCERNS | P2 CC 先字面折叠 `..` 再解软链，与 CX/OS 不一致 | 不折叠拼接 + `fs.realpathSync.native`；sameProject 同法 |
| 5 | **PASS** | P3 `.git` 后缀碰撞从严拦（接受） | — |

附带发现并修复：CX `analyze()` 未解包取子命令（`env X=1 git push` / `sudo git push` 在 CX 不拦），见 fix-note 1b。

VERDICT: PASS
