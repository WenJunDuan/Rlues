- [P1] vibeCoding/athena/gate/lib/git-project.cjs:67 — 非 leading cd 回退 session cwd，导致 idle 仓执行 `echo done; cd <impl仓>; git push` 被放行，未按实际目标仓 stage 拦截。
- [P1] vibeCoding/athena/gate/rules/h5-shell.cjs:195 — nested push 的 index=null 回退 session cwd；idle 仓执行 `bash -c 'git -C <impl仓> push'` 或 `echo "$(git -C <impl仓> push)"` 均被放行。
- [P2] vibeCoding/athena/gate/cli/run.cjs:155 — docs 仅检查 symlink 路径是否入树；`link.md -> ignored/guide.md` 且 ignored/ 被忽略时，`grep -F word link.md` 仍 provable=true，目标内容变化不会使证据失效。
- [P2] vibeCoding/athena/gate/rules/h5-shell.cjs:150 — 未引用 heredoc 的正文仍按普通 shell 引号扫描；`cat <<EOF\n'$(git push)'\nEOF` 返回无 push，但 bash 实际执行替换。该基线残余未修，也未列为 G-010 限制。
VERDICT: REWORK
AC1/AC2/AC4/AC6 覆盖；AC3/AC5 存在上述缺口。
完整 fixture 独立复跑：227 tests，成功，1 skipped；构建未独立复跑。
未发现 review_ignore 隐藏源码或无关过度设计。
