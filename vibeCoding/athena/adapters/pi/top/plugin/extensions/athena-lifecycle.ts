/**
 * Athena PACE · 生命周期
 * session_start / breadcrumb / compact；每轮追加 core/IRON.md。
 */
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CORE = path.join(HERE, "cc-core");
const IRON = path.join(HERE, "..", "core", "IRON.md");

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
      } catch { /* 非 JSON */ }
    }
  } catch { /* fail-open */ }
  return "";
}

function ironText(): string {
  try {
    return readFileSync(IRON, "utf8").trim();
  } catch {
    return "";
  }
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
    } catch { /* fail-open */ }
  });

  pi.on("session_compact", async (_event: any, ctx: any) => {
    const context = hookContext("compact-restore.cjs", {}, 15000, ctx.cwd ?? process.cwd());
    if (context) pending.push(context);
  });

  pi.on("before_agent_start", async (event: any, ctx: any) => {
    const cwd = ctx.cwd ?? process.cwd();
    const parts: string[] = [];
    if (pending.length) { parts.push(...pending); pending = []; }
    const breadcrumb = hookContext("stage-breadcrumb.cjs", {}, 5000, cwd);
    if (breadcrumb) parts.push(breadcrumb);
    const iron = ironText();
    const out: Record<string, unknown> = {};
    if (parts.length) {
      out.message = { customType: "athena-context", content: parts.join("\n\n---\n\n"), display: false };
    }
    if (iron) {
      const base = typeof event?.systemPrompt === "string" ? event.systemPrompt : "";
      out.systemPrompt = base + (base ? "\n\n" : "") + iron;
    }
    return Object.keys(out).length ? out : undefined;
  });
}
