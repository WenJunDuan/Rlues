# roadmap · playbook

> 从 SKILL.md 下沉的完整正文。热路径只留触发与判据。

## items.yaml

模板 `~/.athena/current/templates/items.yaml`。每个 item：`slug`、`title`、`status`（pending / active / paused / deferred / done / dropped）、`sprint`（CLI 回填）、`path`、`depends_on`（前置 item slug）、`write_set`、`ac`。暂缓写 `deferred: {reason, resume_when}`（`after <item>` 可被 athena status 机判）。

## 工作流

1. 建目录：`.ai_state/roadmap/<slug>/`，从 `~/.athena/current/templates/roadmap.md` 与 `items.yaml` 复制。
2. 调研：派只读 architect（任务写明问题与范围），返回 roadmap.md 草稿（背景 / 总体方案 / 切片）与 items 初稿（slug、title、path、depends_on、write_set、ac）。主 agent 审阅后落盘；architect 不写文件。
3. 用户确认：增删 item、调依赖、调顺序。确认结果与裁定来源写进 `queue.md` 执行序。
4. 选下一个：`status: pending` 且 `depends_on` 全部 done 的第一个 item。
5. 开 sprint：`athena sprint start <roadmap>/<item> --path <P>`（item 自动置 active 并绑定 sprint）。
6. 走完 PACE → `athena ship`（item 置 done，`_index` 归零）。回到第 4 步；`athena status` 显示各 roadmap 进度。全部 done → 告诉用户 roadmap 完成。
7. 暂缓：item 置 `deferred` 并写 `resume_when`；满足条件时 status 标 ready。

## 与 brainstorm、decisions

brainstorm（想法不清）→ roadmap（方向清楚但量大）→ 每个 item 一个 sprint。拆分前读相关 `decisions/`；拆分本身是难回退的选择时写一条 decision。
