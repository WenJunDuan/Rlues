/**
 * athena-pace · 生命周期（athena-10.1 S2）
 * session_start / session_compact 注入 _index 摘要与排队提示；before_agent_start 注入提示并每轮追加 core/IRON.md。
 */
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const IRON = path.join(HERE, "..", "core", "IRON.md");
const HOOK = path.join(HERE, "..", "core", "gate", "hook.cjs");
const load = createRequire(import.meta.url);

/** Context injection is fail-open: a core error only loses this turn's context. */
function gate(type: string, payload: Record<string, unknown>, cwd: string): { context?: string } {
  try { return load(HOOK).run("pi", { ...payload, type, cwd }).output; } catch { return {}; }
}

function ironText(): string {
  try { return readFileSync(IRON, "utf8").trim(); } catch { return ""; }
}

export default function (pi: ExtensionAPI) {
  let pending: string[] = [];

  pi.on("session_start", async (_event: any, ctx: any) => {
    const out = gate("session_start", {}, ctx.cwd ?? process.cwd());
    if (out.context) pending.push(out.context);
  });

  pi.on("session_compact", async (_event: any, ctx: any) => {
    const out = gate("session_compact", {}, ctx.cwd ?? process.cwd());
    if (out.context) pending.push(out.context);
  });

  pi.on("before_agent_start", async (event: any, ctx: any) => {
    const parts = pending;
    pending = [];
    const out = gate("before_agent_start", {}, ctx.cwd ?? process.cwd());
    if (out.context) parts.push(out.context);
    const iron = ironText();
    const result: Record<string, unknown> = {};
    if (parts.length) result.message = { customType: "athena-context", content: parts.join("\n\n---\n\n"), display: false };
    if (iron) {
      const base = typeof event?.systemPrompt === "string" ? event.systemPrompt : "";
      result.systemPrompt = base + (base ? "\n\n" : "") + iron;
    }
    return Object.keys(result).length ? result : undefined;
  });
}
