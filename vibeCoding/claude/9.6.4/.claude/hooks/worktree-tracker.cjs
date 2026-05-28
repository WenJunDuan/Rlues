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

  // === [契约] WorktreeCreate hook 必须在 stdout 输出 worktreePath ===
  // CC harness 调 generator 等 subagent (含 isolation: worktree) 时, 会调本 hook
  // 期望 echo path 到 stdout (或 JSON {"hookSpecificOutput":{"worktreePath":...}}).
  // 静默 exit 0 → harness 报 "hook succeeded but returned no worktree path" 阻塞 spawn.
  // 此处优先用 payload 中的 path; 缺失时回落到 JSON 空对象, harness 自行处理 (不阻塞).
  if (eventName === "WorktreeCreate") {
    if (worktreePath) {
      // 直接 echo plain path (harness 接受这种形式)
      process.stdout.write(worktreePath);
    } else {
      // payload 没给 path: 输出 JSON {} 表示 hook 不持有意见, 让 harness 自决
      process.stdout.write(JSON.stringify({ hookSpecificOutput: {} }));
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
