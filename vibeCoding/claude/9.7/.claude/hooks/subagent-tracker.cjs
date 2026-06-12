#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC SubagentStop hook
 *
 * 职责:
 *   1. SubagentStop 触发时, 写 sprints/{current_slug}/subagent-log.md
 *   2. 更新 _index.md.last_subagent + last_subagent_at
 *   3. 若 subagent = generator/polish_worker → 视为 sprint 推进, 检查 stage 转换
 *   4. 若 _index.current_roadmap_slug 非空 + 当前 sprint ship 完成 → 自动推进 roadmap items.yaml
 *
 * 输入: SubagentStop JSON payload (subagent_name, duration_ms, exit_code, last_assistant_message)
 * 源: https://code.claude.com/docs/en/hooks-guide
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
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
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

function checkRoadmapAdvance(aiState, idxFm) {
  const roadmapSlug = idxFm.current_roadmap_slug || "";
  const sprintSlug = idxFm.current_sprint_slug || "";
  if (!roadmapSlug || !sprintSlug) return;

  const itemsPath = path.join(aiState, "roadmap", roadmapSlug, "items.yaml");
  if (!fs.existsSync(itemsPath)) return;

  // 简化: 不完整 YAML 解析, 用文本扫描找 sprint_slug 匹配的 item, 把 status 改 completed
  // (真实实现可用 yaml 包, 但避免外部依赖)
  let content = fs.readFileSync(itemsPath, "utf-8");
  const lines = content.split("\n");
  let foundItemBlock = -1;
  let foundStatusLine = -1;
  for (let i = 0; i < lines.length; i++) {
    if (
      lines[i].includes(`sprint_slug: "${sprintSlug}"`) ||
      lines[i].includes(`sprint_slug: ${sprintSlug}`)
    ) {
      foundItemBlock = i;
      // 在附近找 status 行 (前后 5 行)
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

    // 选下个 pending item (拓扑排序简化版)
    const nextPending = findNextPending(lines);
    if (nextPending) {
      updateFrontmatterField(
        path.join(aiState, "_index.md"),
        "next_action",
        `next_roadmap_item:${nextPending}`,
      );
    } else {
      // 全部 completed, roadmap 结束
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
  // 简化: 找第一个 status: pending 的 slug
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === "status: pending") {
      // 在附近找 slug 行
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

    const subagentName =
      payload?.subagent_name || payload?.subagent_type || "unknown";
    const lastMessage = payload?.last_assistant_message || "";
    const durationMs = payload?.duration_ms || 0;
    const exitCode = payload?.exit_code != null ? payload.exit_code : 0;

    const aiState = findAiState(process.cwd());
    if (!aiState) {
      process.exit(0);
    }

    const idxPath = path.join(aiState, "_index.md");
    if (!fs.existsSync(idxPath)) {
      process.exit(0);
    }

    const { fm: idxFm } = readFrontmatter(idxPath);
    const sprintSlug = idxFm.current_sprint_slug || "";

    const ts = new Date().toISOString();

    // 1. v9.6.4 治本: last_subagent/at 是纯活动记录, 写到 gitignore 的 .snapshots/ 不污染 _index 的 git 追踪
    const snapDir = path.join(aiState, ".snapshots");
    if (!fs.existsSync(snapDir)) fs.mkdirSync(snapDir, { recursive: true });
    fs.writeFileSync(
      path.join(snapDir, "last-subagent.txt"),
      `${subagentName} @ ${ts}\n`,
      "utf-8",
    );

    // 2. 写 subagent-log.md
    if (sprintSlug) {
      const duration = `${Math.round(durationMs / 1000)}s`;
      const status = exitCode === 0 ? "success" : `exit ${exitCode}`;
      const summary = (lastMessage || "").slice(0, 200).replace(/\n/g, " ");
      const entry =
        `## ${ts} · ${subagentName}\n` +
        `- Duration: ${duration}\n` +
        `- Exit: ${status}\n` +
        `- Last message: ${summary}\n\n`;
      appendToSubagentLog(aiState, sprintSlug, entry);
    }

    // 3. 若 generator/polish_worker 完成且 stage=ship → 检查 roadmap 推进
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
