# Feature：Athena 9.10 · Pi 端全结构迁移

目标：把 CC 9.9.9 的提示词**结构**迁到 `vibeCoding/pi-agent/9.10/`：skills/PACE/hooks/agents/rules，按 Pi 原生原语适配，不是只拷正文。
允许写集：`vibeCoding/pi-agent/9.10/` + 本 sprint 文书 + 根 README 指针。不装安装态、不升 CC/CX 版本。
完成条件：Pi 包可 `pi install` 或软链到 `~/.pi/agent`；PACE/skills/hooks 有对应落点；啰嗦点记入下次迭代材料。

分诊：新平台包=Feature。非 Hotfix。conf=0.92。旧 Hotfix 恢复见 `../2026-09-13-telegram-style-hotfix/session-log.md`。
依据：Pi 官方 docs（gh api earendil-works/pi）；高星 `earendil-works/pi` 104k、`badlogic/pi-skills` 2519、`ruizrica/agent-pi` 269。

## 完成

- 包：`vibeCoding/pi-agent/9.10/` · 169 文件 · skills 27 · cc-core 21 · prompts 7。
- 映射：`9.10/docs/HOOK-MAP.md` · 来源：`9.10/docs/SOURCES.md`。
- 啰嗦笔记：本目录 `verbosity-notes.md`。
- 未安装、未跑真机 pi；未声称 Feature review PASS。
- 用户纠偏：去掉版本目录。内容并回 `vibeCoding/pi-agent/`；始终 at least 当前 CC。默认只加载 athena-gates / athena-lifecycle。无第三方 npm 插件。
- 最小集清理：删未接线 hook、STUB prompts、agents/、setup/migrate/init/antigravity、my-pi 残留、mcp/open-tui 空配置。来源/映射/啰嗦笔记并入唯一 `README.md`。
- 用户要求留项目初始化：已恢复 `skills/athena-init`（只建 `.ai_state`，默认不探测 CC/CX）。PACE 与本仓 `.ai_state` 一直都在。

## 2026-09-14 task switch

- 已切换到 `2026-09-14-athena-9-9-9-local-hotfix`，不属于本 Feature 的验收。
- 恢复入口：Feature / impl / `next_action: re-route`；原设计与未提交工作保持不动。
- 2026-09-24：被 athena-10-1 S7（Pi 0.87 适配）取代；README 路径漂移入 S0·AC4。本 sprint 不再推进，S9 归档。
