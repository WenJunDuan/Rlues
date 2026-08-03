/**
 * Athena v9.9.6 · pi 端生命周期适配器 (Phase-2)
 *
 * 复用 cc-core/ 原 hooks, 协议转换:
 *   pi session_start           → session-start.cjs    → 状态摘要暂存, 下一轮注入
 *   pi before_agent_start      → stage-breadcrumb.cjs → 每轮 stage 义务面包屑 (≤240B)
 *   pi session_before_compact  → compact-snapshot.cjs → _index.md 快照 (纯副作用)
 *   pi session_compact         → compact-restore.cjs  → 白名单摘要暂存, 下一轮注入
 *
 * 全程 fail-open (与 CC 端 breadcrumb/session-start 一致): 注入坏了不挡路, 门禁另有 athena-gates 兜底。
 * message schema 已对照包内类型定义 (core/extensions/types.d.ts BeforeAgentStartEventResult →
 * Pick<CustomMessage, "customType" | "content" | "display" | "details">)。
 */
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const CORE = path.join(path.dirname(fileURLToPath(import.meta.url)), "cc-core");

function hookContext(script: string, payload: unknown, timeoutMs: number, cwd: string): string {
  try {
    const stdout = execFileSync(process.execPath, [path.join(CORE, script)], {
      input: JSON.stringify(payload ?? {}),
      encoding: "utf8",
      timeout: timeoutMs,
      cwd,
    });
    for (const line of stdout.split("\n")) {
      const t = line.trim();
      if (!t.startsWith("{")) continue;
      try {
        const parsed = JSON.parse(t);
        const context = parsed?.hookSpecificOutput?.additionalContext;
        if (typeof context === "string" && context.trim()) return context;
      } catch { /* 忽略非 JSON 行 */ }
    }
  } catch { /* fail-open */ }
  return "";
}

export default function (pi: ExtensionAPI) {
  let pending: string[] = [];

  pi.on("session_start", async (_event: any, ctx: any) => {
    const context = hookContext("session-start.cjs", {}, 10000, ctx.cwd ?? process.cwd());
    if (context) pending.push(context);
  });

  pi.on("session_before_compact", async (_event: any, ctx: any) => {
    try {
      execFileSync(process.execPath, [path.join(CORE, "compact-snapshot.cjs")], {
        input: "{}", encoding: "utf8", timeout: 5000, cwd: ctx.cwd ?? process.cwd(),
      });
    } catch { /* fail-open: 快照失败不阻断 compact */ }
  });

  pi.on("session_compact", async (_event: any, ctx: any) => {
    const context = hookContext("compact-restore.cjs", {}, 15000, ctx.cwd ?? process.cwd());
    if (context) pending.push(context);
  });

  pi.on("before_agent_start", async (_event: any, ctx: any) => {
    try {
      const cwd = ctx.cwd ?? process.cwd();
      const parts: string[] = [];
      if (pending.length) { parts.push(...pending); pending = []; }
      const breadcrumb = hookContext("stage-breadcrumb.cjs", {}, 5000, cwd);
      if (breadcrumb) parts.push(breadcrumb);
      if (parts.length) {
        return { message: { customType: "athena-context", content: parts.join("\n\n---\n\n"), display: false } };
      }
    } catch { /* fail-open */ }
  });
}
