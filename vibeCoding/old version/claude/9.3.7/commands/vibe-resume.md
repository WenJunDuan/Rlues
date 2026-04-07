---
effort: medium
---
# /vibe-resume — 恢复 (get-your-bearings)

这是 FRESH context — 你没有上次的记忆。

1. `pwd` + `ls -la`
2. `cat .ai_state/state.json` — 总控状态
3. `cat .ai_state/feature_list.json` — 找 passes:false
4. `cat .ai_state/progress.json` — 上次摘要
5. `git log --oneline -10`
6. `[ -f init.sh ] && bash init.sh` — 基线验证
7. 输出恢复摘要, 继续工作
