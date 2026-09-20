---
sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
verified_at: "2026-09-20"
result: PASS
---

# Runtime Verify — heredoc 感知 shell guard（白名单窄形）

实现合入 main（ff，`2dd3636` 顶端，全套 160/160）后以**真实 hook 进程**（stdin PreToolUse payload，CC node + CX python 双端）实跑。

## 测试场景

| # | 场景 | CC/CX | 结论 |
|---|---|---|---|
| S1 | 活体形态 1（`python3 - <<'PYEOF'` 正文奇反引号，改前 BLOCK） | exit=0 双端 | 误拦消除 |
| S2 | `bash <<'EOF'` 正文危险删除命令（解释器族） | exit=2 双端，recursive force removal | 今日拦保持 |
| S3 | `cat <<EOF` 正文注释行内危险替换（改前放行洞） | exit=2 双端 | 洞已封 |
| S4 | `cat <<'EOF' \| bash`（同行尾随） | exit=2 双端 | 不适用=今日拦保持 |
| S5 | `bash <<'EOF'` 正文 git push --force（闸门绕过例） | 仓库 cwd：exit=2 双端「stage=impl; git push requires ship」与基线 guard 逐字同；/tmp cwd：新旧同为放行（无 .ai_state=非 Athena 语义，既有行为） | 零回归（首测 cwd 误用，经基线对照澄清） |
| S6 | `tee -a <path> >/dev/null <<'EOF'` 正文奇反引号+未闭替换（正向） | exit=0 双端 | 窄形放行 |

佐证：160/160 主仓全绿（21 新增含 32 条非窄形等价矩阵 + 6 条解释器族独立钉）；CC==Pi guard/_shell-lex 字节相等；generator 独立对抗验证（22 条文法接受首行真 bash 实跑零正文执行）留档于其报告与测试注释。落盘本档案时安装态旧 guard 又误拦一次（第 7 例活体，形态即 S6 正向样本），改经 Write 工具落盘——新 guard 部署后该路径自然恢复。
