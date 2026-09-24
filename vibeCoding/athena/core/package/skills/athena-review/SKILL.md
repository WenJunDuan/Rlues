---
name: athena-review
description: 独立审查并把结论绑定到源码树：实现与证据就绪、准备 ship 前使用（Bugfix/Feature/Refactor/System 必需，H3）。
---

# athena-review

何时用：实现完成、`athena run` 证据已在当前树上记录之后，ship 之前。Quick/Hotfix 不需要。

1. `athena review prepare` → 得到 run id 与 packet 路径（packet 含 AC、变更文件、当前树证据、review_ignore）。
2. 派一个**独立** reviewer（CC：`reviewer` agent；CX：`reviewer` agent；Pi：`/reviewer` prompt），只给 packet 路径。优先与作者不同的模型家族（A10）。CC 且开启 `cc_workflows` 时可改跑 `athena-review` workflow。
3. 把 reviewer 原样输出存成文件，`athena review accept --run latest --file <输出> --family <anthropic|openai|xai…>`。
4. 非 PASS（退出码 3）：修复 → `athena run` 重跑检查 → 回到第 1 步（新 run；旧 run 作废，无需「绑定」）。
5. accept 退出码 4（source 或验收行在 prepare 后变了）：回到第 1 步。同一份 reviewer 输出只能被一个 run 接受。

完成条件：`athena review show` 显示 PASS 且 `current`。合同全文在 reviewer agent 定义里，主 agent 不改写 reviewer 输出。
