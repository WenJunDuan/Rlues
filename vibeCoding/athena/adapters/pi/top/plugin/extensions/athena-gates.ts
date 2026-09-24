/**
 * athena-pace · 门禁适配（athena-10.1 S2）
 *
 * 进程内调用 vendored 门禁核 `../core/gate/hook.cjs`（与 ~/.athena/<ver>/ 同字节，由 build.mjs 生成）:
 *   tool_call   → pre_tool  （H1 设计先行 / H5 shell 安全）→ {block, reason}
 *   tool_result → post_tool （兜底证据采集）
 *   agent_end   → stop      （ship 时 H2 证据 / H3 审查）→ followUp 纠偏
 * 核心崩溃: tool_call fail-closed（block），其余放行。Pi 0.87 agent_before_settle 硬停见 S7。
 */
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const load = createRequire(import.meta.url);
const HOOK = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "core", "gate", "hook.cjs");

interface GateOut { block?: boolean; stop?: boolean; reason?: string; context?: string; warnings?: string[] }

function gate(type: string, payload: Record<string, unknown>, cwd: string): GateOut {
  try {
    return load(HOOK).run("pi", { ...payload, type, cwd }).output as GateOut;
  } catch (err: any) {
    const reason = `[athena] gate internal error: ${err?.message ?? err}`;
    return type === "tool_call" ? { block: true, reason } : { warnings: [reason] };
  }
}

export default function (pi: ExtensionAPI) {
  let lastStopReason = "";

  pi.on("tool_call", async (event: any, ctx: any) => {
    const out = gate("tool_call", { toolName: event.toolName, input: event.input ?? {} }, ctx.cwd ?? process.cwd());
    if (out.block) return { block: true, reason: out.reason };
  });

  pi.on("tool_result", async (event: any, ctx: any) => {
    gate("tool_result", {
      toolName: event.toolName, input: event.input ?? {}, isError: event.isError,
      exitCode: event.details?.exitCode,
    }, ctx.cwd ?? process.cwd());
  });

  pi.on("agent_end", async (_event: any, ctx: any) => {
    const out = gate("agent_end", {}, ctx.cwd ?? process.cwd());
    if (!out.stop || !out.reason) { lastStopReason = ""; return; }
    if (out.reason === lastStopReason) {
      try { ctx.ui?.notify?.("[athena] 同一 ship 阻断未消解，停止自动纠偏，需人工处理", "warning"); } catch { /* headless */ }
      return;
    }
    lastStopReason = out.reason;
    try {
      pi.sendUserMessage(`[athena · ship 纠偏] ${out.reason}`, { deliverAs: "followUp" });
    } catch {
      try { ctx.ui?.notify?.(out.reason, "error"); } catch { /* headless */ }
    }
  });
}
