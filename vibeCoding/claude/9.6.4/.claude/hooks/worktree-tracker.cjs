#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC WorktreeCreate + WorktreeRemove hook
 *
 * 职责:
 *   1. WorktreeCreate: 写 worktrees.yaml + 更新 _index.active_worktrees
 *   2. WorktreeRemove: 更新 worktrees.yaml.status + 移除 _index.active_worktrees
 *
 * 输入: hook payload (含 worktree_name, worktree_path, branch, event_name)
 * 源: https://code.claude.com/docs/en/worktrees
 */
"use strict";

const fs = require("fs");
const path = require("path");

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, ".ai_state");
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory())
      return candidate;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function getCurrentSprintSlug(aiState) {
  const idxPath = path.join(aiState, "_index.md");
  if (!fs.existsSync(idxPath)) return null;
  const content = fs.readFileSync(idxPath, "utf-8");
  const m = content.match(/current_sprint_slug:\s*["']?([^"\n]+)["']?/);
  return m ? m[1].trim() : null;
}

function updateActiveWorktrees(aiState, worktreeName, action) {
  // action = 'add' | 'remove'
  const idxPath = path.join(aiState, "_index.md");
  const content = fs.readFileSync(idxPath, "utf-8");
  const m = content.match(/^(active_worktrees:\s*)(\[.*?\])/m);
  let current = [];
  if (m) {
    try {
      const raw = m[2];
      if (raw !== "[]") {
        current = raw
          .replace(/[\[\]"]/g, "")
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      }
    } catch (_) {}
  }

  if (action === "add" && !current.includes(worktreeName))
    current.push(worktreeName);
  if (action === "remove") current = current.filter((w) => w !== worktreeName);

  const newLine = `active_worktrees: [${current.map((w) => `"${w}"`).join(", ")}]`;
  if (m) {
    fs.writeFileSync(
      idxPath,
      content.replace(/^active_worktrees:.*$/m, newLine),
      "utf-8",
    );
  } else {
    // 不存在该字段, 在 frontmatter 末尾添加
    const updated = content.replace(/^---\n([\s\S]*?)\n---/, (_, fmBody) => {
      return `---\n${fmBody}\n${newLine}\n---`;
    });
    fs.writeFileSync(idxPath, updated, "utf-8");
  }
}

function appendToWorktreesYaml(aiState, sprintSlug, payload, ts, eventName) {
  const ytPath = path.join(aiState, "sprints", sprintSlug, "worktrees.yaml");
  fs.mkdirSync(path.dirname(ytPath), { recursive: true });

  const worktreeName = payload?.worktree_name || payload?.name || "unknown";
  const worktreePath = payload?.worktree_path || payload?.path || "";
  const branch = payload?.branch || "";

  if (eventName === "WorktreeCreate") {
    if (!fs.existsSync(ytPath)) {
      const header = `sprint_slug: ${sprintSlug}\nworktrees:\n`;
      fs.writeFileSync(ytPath, header, "utf-8");
    }
    const entry =
      `  - name: "${worktreeName}"\n` +
      `    path: "${worktreePath}"\n` +
      `    branch: "${branch}"\n` +
      `    created_at: "${ts}"\n` +
      `    status: active\n`;
    fs.appendFileSync(ytPath, entry);
  } else if (eventName === "WorktreeRemove") {
    if (!fs.existsSync(ytPath)) {
      return;
    }
    let content = fs.readFileSync(ytPath, "utf-8");
    // 找到匹配 name 的 worktree 块, 把 status: active 改为 removed + 加 removed_at
    const re = new RegExp(
      `(- name: "${worktreeName}"[\\s\\S]*?status:)\\s*active`,
    );
    if (re.test(content)) {
      content = content.replace(re, `$1 removed`);
      // 在 status: removed 后追加 removed_at (找到对应位置)
      const re2 = new RegExp(
        `(- name: "${worktreeName}"[\\s\\S]*?status:\\s*removed)\\n`,
      );
      content = content.replace(re2, `$1\n    removed_at: "${ts}"\n`);
      fs.writeFileSync(ytPath, content, "utf-8");
    }
  }
}

function main() {
  // 解析 payload (失败也不阻断: payload 可能为空)
  let payload = {};
  try {
    let data = "";
    try {
      data = fs.readFileSync(0, "utf-8");
    } catch (_) {}
    payload = data ? JSON.parse(data) : {};
  } catch (e) {
    process.stderr.write(
      `[worktree-tracker] payload parse failed: ${e.message}\n`,
    );
  }

  const eventName = payload?.hook_event_name || payload?.event || "";
  const worktreePath = payload?.worktree_path || payload?.path || "";

  // === WorktreeCreate: payload 已带 path 则 echo (raw path 不走 schema 校验) ===
  // CC harness 调 generator 等 subagent (含 isolation: worktree) 时会调本 hook.
  // 注意: 本 harness 的 hook 输出 schema 不接受 WorktreeCreate 的 hookSpecificOutput
  // (仅 PreToolUse/UserPromptSubmit/PostToolUse/PostToolBatch 合法), 输出它会被拒
  // 并阻断 worktree 创建. 故无 path 时不输出 JSON, 留空让 harness 走默认 provider.
  if (eventName === "WorktreeCreate") {
    if (worktreePath) {
      // 直接 echo plain path (harness 接受这种形式, 不走 schema 校验)
      process.stdout.write(worktreePath);
    } else {
      // payload 没给 path: hook 不当 provider. 检测项目根是否 git repo.
      const cwd = process.cwd();
      const cwdHasGit = fs.existsSync(path.join(cwd, ".git"));
      if (!cwdHasGit) {
        // monorepo / 多子仓库: 项目根非 git, harness 没有"默认 git repo"可建 worktree.
        // 显式拒绝 + 提示用户走手动 worktree 路径.
        process.stdout.write(
          JSON.stringify({
            hookSpecificOutput: { hookEventName: "WorktreeCreate" },
            continue: false,
            stopReason: `项目根 ${cwd} 非 git repo (monorepo 多子仓库结构), isolation:worktree 不可用。请改用 general-purpose subagent + Bash 手动 git worktree add, 或在单一子仓库内启动会话。`,
          }),
        );
      } else {
        // 项目根是 git repo: 不输出 stdout, 让 harness 用默认 provider 创建 worktree.
        // (见上方注释: 输出 hookSpecificOutput.hookEventName 会被 schema 拒绝并阻断.)
      }
    }
  }

  // === 跟踪 (best-effort, 失败不阻断 stdout 已写出的 contract) ===
  try {
    if (!["WorktreeCreate", "WorktreeRemove"].includes(eventName)) {
      process.exit(0);
    }

    const aiState = findAiState(process.cwd());
    if (!aiState) {
      process.exit(0);
    }

    const sprintSlug = getCurrentSprintSlug(aiState);
    if (!sprintSlug) {
      process.exit(0);
    }

    const ts = new Date().toISOString();
    const worktreeName = payload?.worktree_name || payload?.name || "unknown";

    appendToWorktreesYaml(aiState, sprintSlug, payload, ts, eventName);

    if (eventName === "WorktreeCreate") {
      updateActiveWorktrees(aiState, worktreeName, "add");
    } else {
      updateActiveWorktrees(aiState, worktreeName, "remove");
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write(
      `[worktree-tracker] tracking failed (non-blocking): ${e.message}\n`,
    );
    process.exit(0);
  }
}

main();
