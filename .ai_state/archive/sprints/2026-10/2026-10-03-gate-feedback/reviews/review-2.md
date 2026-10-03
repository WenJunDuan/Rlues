- [P1] vibeCoding/athena/gate/rules/h5-shell.cjs:152 — heredoc 正文替换前缀被当作执行上下文；impl 仓执行 `cat <<EOF\ncd <idle仓>;\n$(git push)\nEOF` 被放行，实际正文 cd 是数据，push 仍作用于 impl 仓。
- [P1] vibeCoding/athena/gate/lib/git-project.cjs:82 — contextOnly 遇到前面的 push 提前返回，漏掉后续 cwd 变化；idle 仓执行 `git -C <idle仓> push; cd <impl仓>; bash -c "git push"` 被放行。
VERDICT: REWORK
上一轮四项发现已修；本轮新增两处目标仓漏判均已实测。
G-008/G-010 当前回归：9 tests 通过；最终完整测试和构建仍需覆盖修正后的树。
