# Fix note

| 反馈 | 提交 | 红→绿证据 |
|---|---|---|
| G-006 | 0a44bdd | test_feedback_g006.py：athena run 先失败、后成功 |
| G-007 | 101769c | test_feedback_g007.py：athena run 先失败、后成功 |
| G-008 | 443b711 | test_feedback_g008.py：athena run 先失败、后成功 |
| G-009 | 0d9ae7d | test_feedback_g009.py：athena run 先失败、后成功 |
| G-010 | 18a9b72 | test_feedback_g010.py：athena run 先失败、后成功 |
| G-011 | 4342ee1 | test_feedback_g011.py：athena run 先失败、后成功 |

最终验证：`athena run --covers AC1,AC2,AC3,AC4,AC5,AC6,AC7 -- python3 -m unittest discover -s vibeCoding/athena/evals/fixtures`：234 tests，233 通过、1 skipped（pytest 未安装），100.466s；证据 df92b4a93254，tree bd90702d2880。

`node vibeCoding/athena/build.mjs`：claude/athena/codex/pi 四个平台成功；VERSION 保持 10.1.0。G-011 对 60bc7ed 的 policy 216 组比较：0 个 false→true。

独立 review 历史原文：reviews/review-1.md、review-2.md、review-3.md；各轮发现均有真实复现并折回 G-008/G-010 对应提交。当前审查见 review.json。

残余：G-010 hook 只能整条 allow/block，不能安全拆执行复合调用；G-011 ③ NODE_ENV / *RC 放行违反安全单调，保留基线判定。FEEDBACK.md 同步注明。未安装、未推送。
