# Athena 10.1.5 范围裁定与目录整理（2026-10-05）

结论：用户裁定方案 A，10.1.5 只承诺安装器形态，CC / Codex 插件壳标 experimental。U-001 根因是 Codex 上游 bug，当前清单下 hooks 不缺失。修 1 处 writer 解析缺陷、1 处测试对 node reporter 的依赖；vibeCoding/athena 文档收进 `docs/`。

## U-001 根因

| 项 | 内容 |
|---|---|
| 现象 | cx-plugin 根 `plugin.json` 加 Agent Plugins `$schema` 后 hooks=[]，无报错 |
| 根因 | openai/codex#47925：带 `$schema` 即按 AgentPlugin 格式加载，`codex-rs/core-plugins/src/loader.rs` 对该格式直接返回空，跳过 `load_plugin_hooks()`；`extensions.com.openai.hooks` 被解析但不加载。issue 报于 0.156.1 / 0.157.0，本机 0.160.0 同样复现，未修 |
| 旁证 | DietrichGebert/ponytail#1021（2026-10-04）因同一问题删掉 `$schema` |
| 当前形态 | 不带 `$schema`：Codex 按默认 `hooks/hooks.json` 发现 8 hooks（本机实测），hooks 不缺；代价仅根清单 description 不被读取 |
| 处置 | 保持不带 `$schema`；U-001 降为 P2 上游跟踪，修复后再加并复跑 P6 |

## 缺陷与修复

| ID | 级别 | 触发 / 后果 | 处置 |
|---|---|---|---|
| T1 | P3 | git < 2.38（如 Ubuntu 22.04 的 2.34）时 `writer collect` 走旧版 `merge-tree`，按首字符非空白切块把文件头与 `+<<<<<<<` 冲突块切开，冲突文件名恒为 `(unnamed path)`；拒绝行为本身正确 | 按小写文件头切块（`writer.cjs`）；git 2.34 下 `test_writer_cli` 13 项通过 |
| T2 | 测试 | `test_explicit_env_shell_replay_applies_to_all_segments` 按子串计数，Node 22 非 TTY 用 TAP reporter，每条用例名出现两次 → 4 ≠ 2 | 改为数通过行（TAP `ok N -` / spec `✔`） |

版本号：源码、构建 manifest、两个插件清单、Pi package 均为 10.1.5；产物目录 10.1 与 state version 10.1 按设计保留。另把 `.ai_state/README.md` 里过时的 `Athena 10.1.0` 和 `roadmap athena-10-1` 更正。

## 目录整理

| 变更 | 说明 |
|---|---|
| `vibeCoding/athena/{INSTALL,MIGRATION,RELEASE}.md` → `docs/` | 根目录只留 VERSION、build.mjs 和源码目录 |
| `adapters/core/top/CHANGELOG.md` → `docs/CHANGELOG.md` | 四份发布文档同处；`adapters/core/platform.json` 的 `root_docs` 加入 CHANGELOG |
| 删 `adapters/{cc,cx}/top/` 下 5 个指针文档 | 只写「见 vibeCoding/athena/」；装机后原落 `~/.athena/10.1/docs/{claude,codex}/` |
| `FEEDBACK.md` → `.ai_state/docs/research/athena-downstream-feedback.md` | 下游反馈属外部输入；`athena issue add --type gate` 的追加目标需同步改配置 |
| `build.mjs` 留在根目录 | 唯一构建入口；默认 `--src` 取自身目录，测试复制整棵源码树后执行它 |

dist 产物内容不变，只有 manifest 的 source 字段变化，加上 claude / codex 少了 5 个指针文件。

## 验证

Linux 沙箱（Python 3.10、Node 22、git 2.34）全量 329 项：327 项通过，1 项跳过（缺 pytest），2 项报错（缺 `tomllib`，Python 3.10 环境限制，与本次改动无关）。`build.mjs --check` 通过，`vibeCoding/dist` 已重建。正式证据仍以 macOS 上 `athena run` 复跑为准。

## 剩余发布门（S7）

真机 `athena install --platform cc,cx` → `athena doctor` 无 drift → 安装器形态跑一个 Quick sprint 到 ship（P8）→ `athena rollback` 可回 → 用户确认后打 tag。
