---
sprint_slug: "2026-09-24-s1-single-source-build"
path: "System"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s1-single-source-build"
branch: "athena-10.1"
base_commit: "8903233"
---

# Design — S1 · 单源构建（零行为变化）

> 10.1 设计真相见 `roadmap/athena-10-1/design.md` §3–4、§9.5。本片只建单源与构建，**生成物与 9.9.9(+S0) 逐字节一致**；内容收敛（CC/CX 分叉文件合一、宪法重写）留给 S2/S5。

## 背景 (context)

CC 包 151 + 包外 2 = 153 文件、CX 包 152 + 包外 3 = 155 文件、Pi 独立 86 个；CC/CX 包内同名 110 个，其中 67 个逐字节一致、7 个只差 `~/.claude/skills`↔`~/.agents/skills`、36 个真分叉。每次修改要手工同步多处（compound learning-cross-port-divergence）。

## 方案

- `vibeCoding/athena/`：`core/package/`（CC/CX 共享，74 个，7 个用 `{{athena:SKILLS_DIR}}`）、`adapters/{cc,cx}/package/`（平台独有 + 真分叉）、`adapters/{cc,cx}/top/`（包外 RELEASE 等）、`adapters/pi/top/`（Pi 整包，S2 前不拆）、`core/pace/stages.yaml`。
- `build.mjs`（零依赖 Node）：按平台合成 → `vibeCoding/dist/<p>/10.1/`；来源冲突即失败；模板变量 `{{athena:NAME}}` 未定义即失败；模式归一（可执行 0755，其余 0644）；写 `manifest.json`（sha256/mode/source，排序）、`GENERATED.md`、`contracts.json`。`--check` 对比已有输出。
- 导入一次性完成（脚本不入库，方法记入 session-log）；`vibeCoding/dist/` 开发期 gitignore，发布时（S9）再定是否入库。

### 与 10.1 设计的偏差（已裁量）

| 设计原文 | S1 做法 | 理由 |
|---|---|---|
| 每个生成文件首行头注 | 根目录 `GENERATED.md` + `manifest.json` 标记全部生成物；doctor（S6）按 sha 发现手改 | 首行头注会破坏 SKILL.md frontmatter、脚本 shebang、JSON，且违背「逐字节一致」基线 |
| stages.yaml 生成 stages.md | S1 只生成 `contracts.json`，并用测试核对 stages.yaml 与三份 stages.md 标题一致；stages.md 改为生成物在 S5 | 零行为变化；CC/CX stages.md 仍有平台措辞差异 |
| stages 表未列 plan | stages.yaml 按 9.9.9 实际：brainstorm/roadmap/plan/design/impl/runtime-verify/polish/review/ship | 忠于现状 |
| stages.yaml 用 YAML | JSON 语法书写（YAML ⊃ JSON），`#` 行注释由 build 剥除 | 构建零依赖 |

## 验收标准 (Done Contract)

- AC1: `vibeCoding/athena/` 骨架与 `build.mjs` 存在；`node vibeCoding/athena/build.mjs` 生成 `vibeCoding/dist/{claude,codex,pi}/10.1/`，每端含 `manifest.json`、`GENERATED.md`、`contracts.json`。
- AC2: 生成物与 `claude/9.9.9`、`codex/9.9.9`、`pi-agent/` 逐文件逐字节一致（除上述 3 个新增文件；忽略 `__pycache__`、`.DS_Store`）。
- AC3: 同输入构建两次，全部输出（含 manifest）逐字节一致。
- AC4: 未定义 `{{athena:X}}` 与 core/adapter 同路径冲突都使构建非零退出并点名文件。
- AC5: `contracts.json` 由 `core/pace/stages.yaml` 生成；stages 的 9 个 id 在 CC/CX/Pi 三份 stages.md 均有 `## <id>` 标题；manifest 的 sha 与文件一致。
- AC6: `vibeCoding/athena/evals/fixtures/test_build.py` 覆盖 AC1–AC5；athena999 全量不回归。

## 允许写集

`vibeCoding/athena/**`、`.gitignore`（加 `vibeCoding/dist/`）、本 sprint 文书、`_index.md`、`roadmap/athena-10-1/items.yaml`。不改 `claude/`、`codex/`、`pi-agent/`（冻结基线）。

## 不做

合并 36 个真分叉文件（S5）；门禁代码（S2）；安装器（S6）；Pi 拆分共享（S2/S7）。
