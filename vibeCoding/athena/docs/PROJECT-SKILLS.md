# Quantum project skills

四个产品 skill 的真源为 `core/package/project-packs/quantum/skills/`，不再进入全局 `skills/`。
`build.mjs` 保持现有映射机制：CC/CX 随 core package 携带未激活的 `project-packs/`；Pi 与两个插件壳通过 `core_map` 携带同一项目包。无需新增构建分支。

| 产物 | 未激活项目包（相对该 release） | 项目内启用位置 |
|---|---|---|
| claude | `.claude/project-packs/quantum/skills/` | `<project>/.claude/skills/` |
| codex | `.codex/project-packs/quantum/skills/` | `<project>/.agents/skills/` |
| pi | `project-packs/quantum/skills/` | `<project>/.agents/skills/` |
| claude-plugin / codex-plugin | `project-packs/quantum/skills/` | 同对应平台 |

安装负责人仅在 Quantum 项目中复制上述四个 skill 目录至启用位置，不把整个项目包加入全局扫描。项目已存在同名内容时先核对差异；本次不执行复制或安装。
升级安装时，仅退役安装记录中的旧产品文件（由现有 backup/rollback 保存），不迁移未记录的用户文件。
PACE 保留在全局；项目包从当前 harness 的 skill 索引定位 pace，再读取其参考文件。产品 skill 互为兄弟目录，biz-delivery-loop → `../quantum-codegen/SKILL.md` 保持可解析。
项目包不依赖插件环境变量，复制后同样从当前 skill 索引定位 pace。

## 方案依据（2026-11-17）

- [CC skills](https://code.claude.com/docs/en/skills#frontmatter-reference) 官方已支持 `paths`，它约束自动激活，不能据此断言其他 harness 会隐藏索引。选择项目包以统一三个平台的全局列表行为。
- [CC 项目 skill](https://code.claude.com/docs/en/skills#choose-where-skills-load)、[Codex 项目 skill](https://developers.openai.com/codex/skills)、[Pi 官方源码文档](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md) 支持项目发现；Pi 官方当前明确支持 `.agents/skills/`。
- [Agent Skills 规范](https://agentskills.io/specification)：name 与目录对齐，资源按相对路径组织。
- fixture 验证构建位置、列表排除及本地引用；真实 CC/CX/Pi 会话的项目加载仍待安装负责人验证。
