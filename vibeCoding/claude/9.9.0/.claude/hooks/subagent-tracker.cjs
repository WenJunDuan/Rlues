#!/usr/bin/env node
/**
 * VibeCoding Athena v9.9.2 · CC SubagentStop hook
 *
 * 职责:
 *   1. SubagentStop 触发时, 写 sprints/{current_slug}/subagent-log.md
 *   2. 更新 _index.md.last_subagent + last_subagent_at
 *   3. 若 subagent = generator/polish_worker → 视为 sprint 推进, 检查 stage 转换
 *   4. 若 _index.current_roadmap_slug 非空 + 当前 sprint ship 完成 → 自动推进 roadmap items.yaml
 *   5. v9.8.0 新 (Loop Engineering 闭环): generator 完成且 stage=impl 且 checklist 全完成
 *      → 写 next_action (System/Refactor=runtime-verify, 其余=review). 软驱动, 不绕门禁.
 *
 * 输入: SubagentStop JSON payload (agent_type, agent_id, last_assistant_message, cwd, stop_hook_active)
 *   注: 官方字段是 agent_type/agent_id, 非 subagent_name/subagent_type; 且不含 duration_ms/exit_code.
 * 源: https://code.claude.com/docs/en/hooks (SubagentStop input)
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

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

// 缺陷1 修复 (v9.9.2): subagent 在隔离 worktree 运行时, findAiState 从 worktree cwd
// 向上命中的是 worktree 内的 .ai_state 副本; 写入随 worktree 清理一起丢失, 主仓库缺条目,
// 致 delivery-gate 的 generator 记录检查误报. 检测到 cwd 处于 git worktree 时
// (git-dir != git-common-dir) 重定向到主仓库 .ai_state.
function redirectToMainRepo(aiState, cwd) {
  try {
    const opt = { cwd, encoding: "utf-8", stdio: ["ignore", "pipe", "ignore"] };
    const gitDir = execFileSync("git", ["rev-parse", "--git-dir"], opt).trim();
    const commonDir = execFileSync("git", ["rev-parse", "--git-common-dir"], opt).trim();
    // 主仓库: 两者指向同一 .git → 不重定向
    if (path.resolve(cwd, gitDir) === path.resolve(cwd, commonDir)) return aiState;
    // worktree: 主仓库根 = dirname(common-dir) (通常 <main>/.git)
    const mainAiState = path.join(path.dirname(path.resolve(cwd, commonDir)), ".ai_state");
    if (fs.existsSync(mainAiState) && fs.statSync(mainAiState).isDirectory()) return mainAiState;
  } catch (_) {
    // 非 git 仓库 / git 不可用 → 保持原路径, 不影响非 worktree 场景
  }
  return aiState;
}

function readFrontmatter(filePath) {
  const content = fs.readFileSync(filePath, "utf-8");
  if (!content.startsWith("---")) return { fm: {}, body: content };
  const parts = content.split("---", 3);
  if (parts.length < 3) return { fm: {}, body: content };
  const fm = {};
  for (const line of parts[1].split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const m = t.match(/^([\w\-_.]+)\s*:\s*(.*)$/);
    if (m) {
      let v = m[2].trim();
      // v9.9.1 fix: 取首对引号内的值 (而非剥首尾字符), 防止行尾注释被并入值
      // 例: current_sprint_slug: "xxx"  # 注释 "示例" — 旧逻辑会把注释当值的一部分
      const q = v.match(/^"([^"]*)"|^'([^']*)'/);
      if (q) {
        v = q[1] !== undefined ? q[1] : q[2];
      } else {
        const hashIdx = v.indexOf(" #");
        if (hashIdx >= 0) v = v.slice(0, hashIdx).trim();
      }
      fm[m[1]] = v;
    }
  }
  return { fm, body: parts[2] };
}

function updateFrontmatterField(filePath, field, value) {
  const content = fs.readFileSync(filePath, "utf-8");
  const re = new RegExp(`^(${field}\\s*:\\s*).*$`, "m");
  const newLine = `${field}: ${typeof value === "string" ? `"${value}"` : value}`;
  if (re.test(content)) {
    fs.writeFileSync(filePath, content.replace(re, newLine), "utf-8");
  } else {
    // 字段不存在, 在 frontmatter 末尾插入
    const updated = content.replace(/^---\n([\s\S]*?)\n---/, (_, fmBody) => {
      return `---\n${fmBody}\n${newLine}\n---`;
    });
    fs.writeFileSync(filePath, updated, "utf-8");
  }
}

function appendToSubagentLog(aiState, sprintSlug, entry) {
  const logPath = path.join(aiState, "sprints", sprintSlug, "subagent-log.md");
  fs.mkdirSync(path.dirname(logPath), { recursive: true });
  if (!fs.existsSync(logPath)) {
    fs.writeFileSync(logPath, `# Subagent Log — ${sprintSlug}\n\n`, "utf-8");
  }
  fs.appendFileSync(logPath, entry);
}

// v9.8.0: 检查 impl 的 checklist 是否全完成 (无 pending/in_progress)
function implTasksComplete(aiState, sprintSlug) {
  if (!sprintSlug) return true;
  const cl = path.join(aiState, "sprints", sprintSlug, "checklist.yaml");
  if (!fs.existsSync(cl)) return true; // 无 checklist (绿区小改) → 视为完成
  const content = fs.readFileSync(cl, "utf-8");
  return !/status:\s*(pending|in_progress)/.test(content);
}

function checkRoadmapAdvance(aiState, idxFm) {
  const roadmapSlug = idxFm.current_roadmap_slug || "";
  const sprintSlug = idxFm.current_sprint_slug || "";
  if (!roadmapSlug || !sprintSlug) return;

  const itemsPath = path.join(aiState, "roadmap", roadmapSlug, "items.yaml");
  if (!fs.existsSync(itemsPath)) return;

  // 简化: 不完整 YAML 解析, 用文本扫描找 sprint_slug 匹配的 item, 把 status 改 completed
  let content = fs.readFileSync(itemsPath, "utf-8");
  const lines = content.split("\n");
  let foundStatusLine = -1;
  for (let i = 0; i < lines.length; i++) {
    if (
      lines[i].includes(`sprint_slug: "${sprintSlug}"`) ||
      lines[i].includes(`sprint_slug: ${sprintSlug}`)
    ) {
      for (let j = Math.max(0, i - 5); j < Math.min(lines.length, i + 5); j++) {
        if (lines[j].trim().startsWith("status:")) {
          foundStatusLine = j;
          break;
        }
      }
      break;
    }
  }

  if (foundStatusLine >= 0) {
    lines[foundStatusLine] = lines[foundStatusLine].replace(
      /status:\s*\w+/,
      "status: completed",
    );
    fs.writeFileSync(itemsPath, lines.join("\n"), "utf-8");

    const nextPending = findNextPending(lines);
    if (nextPending) {
      updateFrontmatterField(
        path.join(aiState, "_index.md"),
        "next_action",
        `next_roadmap_item:${nextPending}`,
      );
    } else {
      updateFrontmatterField(
        path.join(aiState, "_index.md"),
        "current_roadmap_slug",
        "",
      );
      updateFrontmatterField(
        path.join(aiState, "_index.md"),
        "next_action",
        "roadmap_complete",
      );
    }
  }
}

function findNextPending(lines) {
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === "status: pending") {
      for (let j = Math.max(0, i - 5); j < Math.min(lines.length, i + 5); j++) {
        const m = lines[j].match(/slug:\s*["']?([\w-]+)["']?/);
        if (m) return m[1];
      }
    }
  }
  return null;
}

function main() {
  try {
    let data = "";
    try {
      data = fs.readFileSync(0, "utf-8");
    } catch (_) {}
    const payload = data ? JSON.parse(data) : {};

    // 缺陷2 修复 (v9.9.2): 官方 SubagentStop payload 字段是 agent_type / agent_id
    // (不是 subagent_name/subagent_type); 后者恒 undefined → 日志恒 "· unknown",
    // delivery-gate 只能靠 last message 碰巧含 "generator" 字样. 保留旧字段兜底防平台再改.
    const subagentName =
      payload?.agent_type || payload?.subagent_name || payload?.subagent_type || "unknown";
    const agentId = payload?.agent_id || "";
    const lastMessage = payload?.last_assistant_message || "";

    // 缺陷1: 官方 SubagentStop 带 cwd 字段, 优先用它 (比 process.cwd() 更贴合触发上下文)
    const cwd = payload?.cwd || process.cwd();
    let aiState = findAiState(cwd);
    if (!aiState) {
      process.exit(0);
    }
    aiState = redirectToMainRepo(aiState, cwd);

    const idxPath = path.join(aiState, "_index.md");
    if (!fs.existsSync(idxPath)) {
      process.exit(0);
    }

    const { fm: idxFm } = readFrontmatter(idxPath);
    const sprintSlug = idxFm.current_sprint_slug || "";

    const ts = new Date().toISOString();

    // 1. last_subagent/at 写到 gitignore 的 .snapshots/ 不污染 _index 的 git 追踪
    const snapDir = path.join(aiState, ".snapshots");
    if (!fs.existsSync(snapDir)) fs.mkdirSync(snapDir, { recursive: true });
    fs.writeFileSync(
      path.join(snapDir, "last-subagent.txt"),
      `${subagentName} @ ${ts}\n`,
      "utf-8",
    );

    // 2. 写 subagent-log.md
    // 官方 SubagentStop payload 不含 duration_ms/exit_code (仅 agent_type/agent_id/
    // last_assistant_message/stop_hook_active), 故不再写编造的 Duration/Exit;
    // 记 agent_id + last_assistant_message 前 200 字作为证据. 失败感知由 subagent-retry hook 承担.
    if (sprintSlug) {
      const summary = (lastMessage || "").slice(0, 200).replace(/\n/g, " ");
      const entry =
        `## ${ts} · ${subagentName}\n` +
        (agentId ? `- Agent ID: ${agentId}\n` : "") +
        `- Last message: ${summary}\n\n`;
      appendToSubagentLog(aiState, sprintSlug, entry);
    }

    // 3. v9.8.0 (Loop Engineering 闭环): generator 完成且 stage=impl 且 checklist 全完成
    //    → 写 next_action 软驱动下一步. System/Refactor=runtime-verify, 其余=review.
    //    (仅当 generator 成功; 失败不推进, 由 subagent-retry hook 记录)
    // exit_code 官方 payload 不提供 → 用 implTasksComplete (checklist 全 complete) 作为
    // 真正的完成信号; generator 失败时 checklist 不会全绿, 自然不推进.
    if (
      subagentName === "generator" &&
      idxFm.stage === "impl" &&
      implTasksComplete(aiState, sprintSlug)
    ) {
      const pathType = idxFm.path || "";
      const rtSkip =
        (idxFm.skip_runtime_verify || "false").toString().toLowerCase() ===
        "true";
      const nextAct =
        !rtSkip && (pathType === "System" || pathType === "Refactor")
          ? "runtime-verify"
          : "review";
      updateFrontmatterField(idxPath, "next_action", nextAct);
    }

    // 4. 若 generator/polish_worker 完成且 stage=ship → 检查 roadmap 推进
    if (
      ["generator", "polish_worker"].includes(subagentName) &&
      idxFm.stage === "ship"
    ) {
      checkRoadmapAdvance(aiState, idxFm);
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write(`[subagent-tracker] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

main();
