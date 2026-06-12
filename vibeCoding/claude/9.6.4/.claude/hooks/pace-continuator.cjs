#!/usr/bin/env node
/**
 * v9.6.2 · CC Stop hook (优先级低于 delivery-gate)
 * 职责: 在 _index.md 末尾追加 "current_sprint stage=X completed @ <ts>" 历史条目
 *       但不阻塞 (delivery-gate 已经做硬约束).
 */
"use strict";
const fs = require("fs");
const path = require("path");

function findAiState(cwd) {
  for (let i = 0, c = cwd; i < 5; i++) {
    const cand = path.join(c, ".ai_state");
    if (fs.existsSync(cand) && fs.statSync(cand).isDirectory()) return cand;
    const p = path.dirname(c);
    if (p === c) return null;
    c = p;
  }
  return null;
}

function main() {
  try {
    const aiState = findAiState(process.cwd());
    if (!aiState) {
      process.exit(0);
    }
    const idx = path.join(aiState, "_index.md");
    if (!fs.existsSync(idx)) {
      process.exit(0);
    }

    // 解析 frontmatter 取当前 stage / sprint
    const content = fs.readFileSync(idx, "utf-8");
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch) {
      process.exit(0);
    }
    const fm = fmMatch[1];
    const stage = (fm.match(/stage:\s*"?([^"\n]+)"?/) || [])[1] || "";
    const sprint = (fm.match(/current_sprint:\s*(\d+)/) || [])[1] || "?";

    if (!stage) {
      process.exit(0);
    }

    // v9.6.4 治本: turn-end 历史写到 gitignore 的 .snapshots/ (不再污染 _index.md 的 git 追踪).
    // 原实现 append 到 _index.md, 且 HIST_MARKER 与实际不符, 每回合追加新 "## 历史" 块 -> 无限增长 + 持续 churn.
    const ts = new Date().toISOString().slice(0, 19).replace("T", " ");
    const entry = `- \`${ts}\`: stage=${stage} sprint=${sprint} turn-end\n`;
    const snapDir = path.join(aiState, ".snapshots");
    if (!fs.existsSync(snapDir)) fs.mkdirSync(snapDir, { recursive: true });
    fs.appendFileSync(path.join(snapDir, "turn-history.log"), entry);
  } catch (e) {
    process.stderr.write(`[pace-continuator] non-blocking: ${e.message}\n`);
  }
  process.exit(0);
}
main();
