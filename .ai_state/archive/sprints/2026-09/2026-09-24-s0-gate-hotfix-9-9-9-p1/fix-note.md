# Fix note — S0 gate-hotfix-9-9-9-p1

| # | 根因 | 修法 | 位置（CC / CX / Pi） |
|---|---|---|---|
| 1 | 推送判定只看 cwd 的 stage，`git -C <其他仓>` / `cd <其他仓> &&` 也被本项目 stage 拦 | `pushTarget` 取最后一个顶层 `cd`（&& 或 ;）与 `git -C`，按目标仓 stage 判；但凡属于**同一项目**（同 git common dir、共享任一远端 URL、远端是本项目本地仓、推送目的地是本项目远端、目的地不可读）仍按本项目 stage；`GIT_DIR` 类变量、`--git-dir/--work-tree`、嵌套推送、无法解析的目录一律回落 cwd | `pre-bash-guard.cjs` / `.py` / Pi 同字节 |
| 1b | CX `analyze()` 用未解包的 args 取子命令，`env X=1 git push`、`sudo git push` 在 CX 不被识别为推送（**既有漏洞**） | 改用解包后的 `vals`，与 CC 一致 | `pre-bash-guard.py` |
| 2 | `git commit -F - <<'EOF'` 正文里的 `git push` 被当命令 | 数据型 consumer 增 `git`、`gh`（窄形 heredoc 正文屏蔽；解释器正文照旧分析） | `_shell-lex.cjs` / `_shell_lex.py` / Pi 同字节 |
| 3 | design 首次落盘即置 `design_changed_after_impl` | 仅 `git cat-file -e HEAD:<design>` 成立才置位；路径按 payload cwd 解析（CC/CX 一致） | `design-change-detector.cjs` / `.py` |
| 4 | 写集里的 `vm-pending.md` 路径被当承诺 | 正则 `vm-pending(?!\.md)`；`path=Quick` 且 design 含 `vm-pending.md` 跳过 | `delivery-gate.cjs` / `.py` |
| 5 | 宪法「CC 无原生 /goal」过期；Pi README 路径不存在；peer `*` | 改为「CC ≥2.1.269 有 /goal」；路径 `vibeCoding/pi-agent/*`；peer `>=0.87 <0.88` | `CLAUDE.md`、Pi 三份 README、`package.json` |
| 6 | `init-platforms.py` 以 `'.claude' in parts` 判端 | `package_platform()`：包目录 `parents[3].name == '.claude'` | CC/CX 两份（同字节） |

## 残留与边界（已知、接受）

- 远端等价按 URL 规范化（https / ssh:// / scp / file:// / 本地真实路径）+ insteadOf 改写判断；**SSH host 别名**（`~/.ssh/config` 的 Host）不在范围。
- 本地远端去掉 `.git` 后比较：`/x/up` 与 `/x/up.git` 视为同一 → 从严拦（有意）。
- 若 `GIT_DIR` 由会话**继承的环境**而非命令文本设置，hook 看不到 → 与修复前相同，无新增。
- Pi 端 delivery-gate 为分叉旧版，无 vm-pending 校验，本片不动（10.1 S2 统一）。
- Pi peer 钉 0.87 未在真机 pi 验证 → 10.1 S7 冒烟。
- 承诺闭合的「登台账/转台账」扩展句式未做（会扩大拦截面）→ 10.1 S2·A4。
