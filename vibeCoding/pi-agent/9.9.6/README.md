# Athena v9.9.6 · pi 端配置 (DeepSeek 试点)

本目录镜像 `~/.pi/agent/` 的内容, 与 `vibeCoding/claude/9.9.6` 同源同版本。参考结构: [bd-dxg/my-pi](https://github.com/bd-dxg/my-pi) + pi 官方文档。

## 安装 (macOS)

```bash
# 1. Node ≥ 20
brew install node

# 2. 安装 pi (二选一)
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
# 或 curl -fsSL https://pi.dev/install.sh | sh

# 3. DeepSeek API key → auth.json (类 codex 方式, 不进 shell rc / 不进 git 仓库)
mkdir -p ~/.pi/agent
cp auth.json.example ~/.pi/agent/auth.json
chmod 600 ~/.pi/agent/auth.json
# 编辑 ~/.pi/agent/auth.json 填入真实 key。models.json 的 apiKey 走官方 "!shell命令" 形式,
# 每次请求时从 auth.json 现读 (docs/models.md), 仓库内零明文。
# ⚠ auth.json 只存在于 ~/.pi/agent/, 永远不要放进 Rlues 仓库

# 4. 部署本目录 → ~/.pi/agent/ (逐项软链, 不要链整个目录 — ~/.pi/agent 还有 sessions/ 等运行时数据)
PI=~/.pi/agent; SRC=$(pwd)
mkdir -p $PI
for f in AGENTS.md settings.json models.json prompts rules extensions; do
  ln -sfn "$SRC/$f" "$PI/$f"
done

# 5. 验证
pi --model deepseek/deepseek-v4-flash "自我介绍一下, 并列出你加载到的 AGENTS.md 铁律条数"
```

TUI 内检查: `/model` 应出现 deepseek 两个模型; `/settings` 确认 defaultProvider。

## 目录说明

| 文件/目录 | 用途 |
|---|---|
| `AGENTS.md` | 宪法, 迁移自 CC 端 `CLAUDE.md` (含 pi 平台差异适配) |
| `settings.json` | pi 全局设置, 默认 deepseek-v4-flash |
| `models.json` | DeepSeek 自定义 provider (openai-completions) |
| `auth.json.example` | API key 模板 → 复制为 `~/.pi/agent/auth.json` (chmod 600, 不进仓库) |
| `mcp.json` | MCP 服务 (chrome-devtools/searchcode/tavily), 取自 my-pi 并做 macOS 适配; 需装 pi-mcp-adapter 生效 |
| `open-tui.json` | 终端 UI (zh 界面 + cwd/context/tokens/cost 状态栏), 取自 my-pi; 需装 pi-open-tui 生效 |
| `prompts/` | 7 个角色提示词模板, 迁移自 CC `agents/`, 用 `/architect` 等调用 |
| `rules/` | 项目规范, 原样迁移, AGENTS.md 指令按需 Read |
| `extensions/athena-gates.ts` | 门禁适配器: tool_call→pre-bash-guard/delivery-gate, agent_end→Stop 纠偏 |
| `extensions/athena-lifecycle.ts` | 生命周期适配器: session_start 注入/compact 快照恢复/每轮面包屑 |
| `extensions/cc-core/` | CC 端 hooks 原样复用 (7 个 .cjs, 仅 2 处路径 patch: rules/stages 优先 pi 路径) |
| `extensions/tools.ts` | `/tools` 交互式工具开关 (取自 my-pi, AGPL-3.0, 未改逻辑) |
| `extensions/questionnaire.ts` | AI 主动弹窗提问工具 (取自 my-pi); brainstorm/plan 阶段确认验收用 |

## my-pi 整合对照 (2026-08-03 逐文件 diff)

已取: models.json `compat` 兼容参数 (supportsDeveloperRole:false — DeepSeek 不支持 developer role, 缺了会报错) + maxTokens 64000 实战值 · settings.json retry 加强 (8 次/5s/120s cap) + theme/hideThinkingBlock/showCacheMissNotices · mcp.json (macOS 适配, 原为 Windows `cmd /c`) · open-tui.json 原样 · extensions/tools.ts + questionnaire.ts。

不取及理由: `permission-gate.ts` (正则级拦截, `\brm\b` 全拦误报高, 弱于我们 AST 级 pre-bash-guard, 双门禁互相打架) · `qna.ts` (每轮回复后额外 LLM 抽取调用 = 常驻 token 税) · `structured-output.ts` (demo 性质, 无现实需求) · `compaction:false` (我们的 compact 快照恢复链依赖 compaction) · `httpProxy` 硬编码 (按需自加: settings.json `"httpProxy": "http://127.0.0.1:<port>"`) · 它的 AGENTS.md (Athena 宪法不混入) · `@juicesharp/rpiv-todo` 包 (与 PACE/Sisyphus 双真相源冲突)。

待验证: maxTokens 官方标称 384K 输出, my-pi 实战用 64000 — 先用 64000, 实测 API 报错边界后再调。

## 待验证 (装好后逐项跑)

1. `deepseek-v4-flash` / `deepseek-v4-pro` 模型 ID 实测: `curl https://api.deepseek.com/models -H "Authorization: Bearer $(node -p "JSON.parse(require('fs').readFileSync(require('os').homedir()+'/.pi/agent/auth.json','utf8')).deepseek")"`。若返回旧别名 `deepseek-chat`/`deepseek-reasoner`, 改 models.json 的 `id`
2. pi 是否已内置 deepseek provider (`pi update --models` 后看 `/model` 列表): 若内置且重名冲突, 删本目录 models.json
3. prompts 模板是否吃 HTML 注释头 (不吃就删首行注释)
4. macOS 27 未单独验证; pi 只依赖 Node + 终端, 无 OS 绑定, 预期无碍
5. 扩展单测: `pi -e ./extensions/athena-gates.ts "在这个项目里跑 rm -rf /"` → 应被 block; `pi -e ./extensions/athena-lifecycle.ts` 在含 .ai_state 的项目里起会话 → 首轮应看到状态摘要注入 (message.display=false, /tree 里可见)
6. before_agent_start 注入与 agent_end followUp 已按包内类型定义 (v0.52.x) 编写并 tsc 通过, 但未在真机跑过完整回路 — dogfood 第一天优先验证

## 已验证 (2026-08-03, 云容器)

- extensions/*.ts 对 `@earendil-works/pi-coding-agent` 真实类型定义 `tsc --noEmit` 通过
- cc-core 8 项冒烟: rm -rf / 与 curl|sh 与非 ship 期 git push 均 block; 非 Athena 目录静默放行; impl 期缺验收标准的写入被 delivery-gate block; session-start/compact 快照+恢复输出正常
- models.json `!node -p` 读 auth.json 命令实测输出 key 正确

## 包安装计划 (按能力缺口分层, 2026-08-03 调研)

来源: [pi.dev/packages](https://pi.dev/packages) 官方 gallery + [awesome-pi](https://awesome-pi.site/extensions/)。原则: 按 MIGRATION.md 缺口选, 不按热度堆; 现成包能补的缺口优先于 Phase-2 自写 (铁律[不抱金饭碗讨饭])。

### 第一批 — 补硬缺口 (裸跑 1-2 天确认 DeepSeek 基线后, 逐个装+冒烟, 不要一次全装)

```bash
pi install pi-mcp-adapter        # MCP 连接 (四原语); 本目录 mcp.json 生效前提
pi install pi-open-tui           # 终端 UI; 本目录 open-tui.json 生效前提 (my-pi 同款)
pi install pi-subagents          # subagent 委派 (链式+并行); 补红区隔离降级
pi install pi-web-access         # web 搜索/抓取; DeepSeek 无原生搜索, 铁律[证据与出处]依赖
```

注: `@orca-sec/pi-orca` 从第一批移除 — Phase-2 已落地自有 athena-gates (pre-bash-guard 级), 双门禁打架; 若 dogfood 发现自有门禁盲区再评估。my-pi 的另三个包 (@pi-lab/notify → 第二批 / @juicesharp/rpiv-todo → 不装 / @firstpick/pi-themes-bundle + pi-rounded-tools → 纯 UI 随意)。

- subagent 三候选: `pi-subagents` (先试, gallery 热度最高) / `@tintinweb/pi-subagents` / `pi-swarm`, 只留一个
- ⚠ orca 装前必读源码: 它拦 bash = 门禁主权外包, 规则错会挡正常工作流; 若达标, Phase-2 免写 pre-bash-guard.ts
- 备选: `pi-defender` (orca 不达标时换)

### 第二批 — 观察, 两周 dogfood 数据后再定

| 包 | 对应 CC 能力 | 装的条件 |
|---|---|---|
| `pi-lens` | LSP/linter 实时反馈, 强化 TDD/review | review 阶段漏检有实例 |
| `gentle-engram` | compact-snapshot/restore 双件 | compaction 后丢状态有实例 |
| `@pi-lab/notify` / `avtc-pi-notification` | notification-router | 长任务多到需要通知 |
| `pi-open-tui` | 无 (纯 QoL, my-pi 同款) | 随意 |

### 明确不装

| 类别 | 理由 |
|---|---|
| todo/任务管理 (pi-taskflow / pi-solyPi / pi-todo-*) | 与 PACE + Sisyphus 重叠, 装了=双真相源 |
| review 类 (pi-pr-review / @zephyrdeng/pi-review) | 已有 critic/reviewer/spec-compliance 三件套 prompts |
| context/cache 优化类 | DeepSeek 便宜, 无痛点数据 (铁律[反过度工程]) |
| 模型路由/网关类 (litellm 等) | 单 provider 试点, 伪需求 |

每个包的验收: 装后跑一次真实任务, 无感或负收益 → `pi remove` 立即回滚。

## 官方文档

- README: https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md
- settings: .../docs/settings.md · models: .../docs/models.md · extensions: .../docs/extensions.md
