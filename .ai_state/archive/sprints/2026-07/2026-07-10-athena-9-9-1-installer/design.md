---
sprint_slug: "2026-07-10-athena-9-9-1-installer"
roadmap_item: "installer-release"
path: "Feature"
created: "2026-07-10"
---

# Design — Installer and Migration

## Scope

实现 release 总设计 AC2、AC10–AC11、AC20–AC21：setup 五态、仓库根定位、AGENTS 首装、动态计数、hook trust 提示；9.9.0→9.9.1 事务迁移；版本与 CHANGELOG；CX skills 迁往官方 `~/.agents/skills`。

## Acceptance

- setup 分别探测 CC/CX：fresh、CC-only、CX-only、same-version；old-version 只路由 migrate。
- fresh CX 复制 AGENTS，skills 安装 `~/.agents/skills`；不直接写 trust store。
- migrate orchestrator 覆盖 CC/CX 配置合并、release-owned 资产、`~/.agents/skills` 与精确 legacy 清理；所选 endpoints 使用单 transaction backup，多文件失败全回滚。
- dry-run、幂等、backup 后/首配置后/资产复制中/post-verify 四阶段故障注入通过；不打印敏感值。
- provider/MCP/projects/desktop/plugins/未知表保持；只清理 Athena 自己的 deprecated skill 副本。
- setup/migrate 双端 frontmatter 合规，版本身份与 CHANGELOG 为 9.9.1。

## Design Review

继承 release 总设计三轮 critic PASS；写集与 CX runtime/shared contract 无重叠。
