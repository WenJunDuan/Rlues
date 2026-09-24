---
name: athena-setup
description: |
  Athena 全局首次配置 (跨项目, 一次性). 从分发包部署 settings/config/rules/standards/hooks/agents/skills 到 ~/.claude/ (CC) 与 ~/.codex/ (CX).
  和 athena-init 区别: setup 全局一次性, init 每项目一次. 已装则转 verify/upgrade (走 athena-migrate).
effort: low
---

# /athena-setup — Athena 全局首次配置 (v9.8.0)

> v9.8.0 修两处历史硬伤: (1) CC 端旧版把 CX skills/standards 装到 `~/.agents/`, 但全 harness (config.toml 注册路径、CX skill 内部互引、session-start standards 查找) 都认 `~/.codex/` —— 装到 `~/.agents/` 等于装了没人读。现统一到 `~/.codex/`。(2) 旧版 cp 用相对 cwd 裸路径、无包定位, 从项目里 `/athena-setup` 触发时无源可 cp。现加 `ATHENA_CC_PKG` / `ATHENA_CX_PKG` 定位 + 幂等。

## Step 0 · 定位分发包 + 判首装/已装 (必做)

```bash
# 分发包里的 .claude / .codex 目录 (本仓库即 vibeCoding/claude/9.8.0/.claude 和 codex/9.8.0/.codex).
# 优先环境变量; 否则尝试 cwd 下常见布局; 找不到就报错让用户显式指定 (绝不凭空生成).
CC_PKG="${ATHENA_CC_PKG:-}"
CX_PKG="${ATHENA_CX_PKG:-}"
for c in "$CC_PKG" "$PWD/.claude" "$PWD/cc/.claude" "$PWD/claude/9.8.0/.claude"; do
  [ -n "$c" ] && [ -f "$c/settings.json" ] && CC_PKG="$c" && break
done
for c in "$CX_PKG" "$PWD/.codex" "$PWD/cx/.codex" "$PWD/codex/9.8.0/.codex"; do
  [ -n "$c" ] && [ -f "$c/config.toml" ] && CX_PKG="$c" && break
done
echo "CC_PKG=$CC_PKG"; echo "CX_PKG=$CX_PKG"
[ -f "$CC_PKG/settings.json" ] || echo "⚠️ 未定位 CC 包: export ATHENA_CC_PKG=<.claude 目录> 再跑"
[ -f "$CX_PKG/config.toml" ]  || echo "⚠️ 未定位 CX 包: export ATHENA_CX_PKG=<.codex 目录> 再跑"

# 幂等: 已装 → 这是校验/升级, 不盲目覆盖
if [ -d ~/.claude/skills ] || [ -d ~/.codex/skills ]; then
  echo "检测到已安装 Athena → 走升级请用 /athena-migrate (备份+迁移); 仅校验则跑下方各 Step 的自检命令."
fi
```

> **chicken-and-egg 提示**: 能跑 `/athena-setup` 说明 CC skills 已在 `~/.claude/skills/`。真正**首装**需先手动 `cp -r "$CC_PKG/skills/"* ~/.claude/skills/` 再用 skill 形态。本 skill 负责**非-skill 资产 + CX 全套 + 校验**。

## CC 端 (~/.claude/)

```bash
mkdir -p ~/.claude/{rules,hooks,agents,skills}
cp "$CC_PKG/settings.json" ~/.claude/settings.json
cp "$CC_PKG/rules/"*.md     ~/.claude/rules/                 # 6: _index + coding/doc/git/security/ui
cp "$CC_PKG/hooks/"*.cjs    ~/.claude/hooks/ && chmod +x ~/.claude/hooks/*.cjs   # 14
cp "$CC_PKG/agents/"*.md    ~/.claude/agents/                # 5: critic/evaluator/generator/reviewer/spec-compliance
cp -r "$CC_PKG/skills/"*    ~/.claude/skills/                # 21 (含 v9.8.0 新增 athena-requirements / athena-issue)
# 自检
echo "rules=$(ls ~/.claude/rules/*.md|wc -l) hooks=$(ls ~/.claude/hooks/*.cjs|wc -l) agents=$(ls ~/.claude/agents/*.md|wc -l) skills=$(ls -d ~/.claude/skills/*/|wc -l)"
```

## CX 端 (~/.codex/) ← 全部落 ~/.codex/, 与 config.toml 注册路径一致

```bash
[ -f ~/.codex/config.toml ] && cp ~/.codex/config.toml ~/.codex/config.toml.pre-athena
mkdir -p ~/.codex/{hooks,agents,standards,skills}
cp "$CX_PKG/config.toml" ~/.codex/config.toml
# 展开 skills.config 里的 <USER_HOME> (portable: 不用 sed -i, 因 BSD/macOS 与 GNU 语义不同)
sed "s|<USER_HOME>|$HOME|g" ~/.codex/config.toml > ~/.codex/config.toml.tmp && mv ~/.codex/config.toml.tmp ~/.codex/config.toml
cp "$CX_PKG/hooks.json"  ~/.codex/hooks.json
cp "$CX_PKG/hooks/"*.py      ~/.codex/hooks/ && chmod +x ~/.codex/hooks/*.py   # 10
cp "$CX_PKG/agents/"*.toml   ~/.codex/agents/                # 9
cp "$CX_PKG/standards/"*.md  ~/.codex/standards/             # 6 (session-start.py 首选此处)
cp -r "$CX_PKG/skills/"*     ~/.codex/skills/                # 21 (config.toml [[skills.config]] 指向此处)
# 自检
echo "hooks=$(ls ~/.codex/hooks/*.py|wc -l) agents=$(ls ~/.codex/agents/*.toml|wc -l) standards=$(ls ~/.codex/standards/*.md|wc -l) skills=$(ls -d ~/.codex/skills/*/|wc -l)"
grep -c '^\[\[skills.config\]\]' ~/.codex/config.toml         # 应 = skills 数 (含新)
grep -c '^\[\[hooks\.'           ~/.codex/config.toml         # 应 = 0 (hooks 走 hooks.json)
```

> **不部署 prompts/**: Codex 自定义 prompt 已 deprecated, 入口统一为 skill (自动发现). 从旧版升级时 `rm -rf ~/.codex/prompts`。

## AG (Antigravity)

不部署. Athena 只调度 `agy`。

## 跨平台部署位置表 (权威, 与 config.toml / session-start / skill 内部引用一致)

| Athena 资产 | CC | CX |
|---|---|---|
| Settings | `~/.claude/settings.json` | `~/.codex/config.toml` + `~/.codex/hooks.json` |
| Rules / Standards | `~/.claude/rules/` (6) | `~/.codex/standards/` (6) |
| Hooks | `~/.claude/hooks/*.cjs` (14) | `~/.codex/hooks/*.py` (10) |
| Subagents | `~/.claude/agents/*.md` (5) | `~/.codex/agents/*.toml` (9) |
| Skills | `~/.claude/skills/` (21) | `~/.codex/skills/` (21) |

## 卸载

```bash
# CC
rm -rf ~/.claude/{rules,hooks,agents,skills}; rm ~/.claude/settings.json
# CX
rm ~/.codex/hooks.json; mv ~/.codex/config.toml.pre-athena ~/.codex/config.toml 2>/dev/null
rm -rf ~/.codex/{hooks,agents,standards,skills}
# 旧版残留 (若以前被 stale setup 装到 ~/.agents/)
rm -rf ~/.agents/skills/_athena ~/.agents/standards
```

## 升级

跑 `/athena-migrate` (备份 → 迁移 → 验证). 不要用 athena-setup 覆盖已装环境。
