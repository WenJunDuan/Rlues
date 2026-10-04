/**
 * athena-pace · 门禁适配（athena-10.1.5 S4）
 *
 * 进程内调用 vendored 门禁核 `../core/gate/hook.cjs`（与 ~/.athena/<ver>/ 同字节，由 build.mjs 生成）:
 *   tool_call           → pre_tool  （H1 设计先行 / H5 shell 安全）→ {block, reason}
 *   tool_result         → post_tool （兜底证据采集）
 *   agent_before_settle → stop      （ship 时 H2 证据 / H3 审查）→ {entries, continue: true} 硬停（Pi ≥ 0.87）
 *   agent_end           → 硬停可用时不评估（否则一次收尾计两次，熔断提前）；Pi < 0.87 回退 followUp 软纠偏
 * 判定与返回形态都在 `core/gate/platform/pi.cjs`（有 fixture），本文件只转发。
 * 防循环: 门禁核熔断（同因 3 次 → 放行 + issues.md 记一行），放行后 render 不再给 continue。
 * codemode: 外层 `codemode` 调用放行；脚本内每个内置工具调用各自触发 tool_call，照常判定。
 * 核心崩溃: tool_call fail-closed（block），其余放行。
 */
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import * as host from "@earendil-works/pi-coding-agent";

const load = createRequire(import.meta.url);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const HOOK = path.join(HERE, "..", "core", "gate", "hook.cjs");
const ADAPTER = path.join(HERE, "..", "core", "gate", "platform", "pi.cjs");

interface StopEntry { type: "custom_message"; customType: string; content: string; display: boolean }
interface GateOut {
  block?: boolean; stop?: boolean; continue?: boolean; reason?: string; context?: string;
  entries?: StopEntry[]; warnings?: string[];
}

function gate(type: string, payload: Record<string, unknown>, cwd: string): GateOut {
  try {
    return load(HOOK).run("pi", { ...payload, type, cwd }).output as GateOut;
  } catch (err: any) {
    const reason = `[athena] gate internal error: ${err?.message ?? err}`;
    return type === "tool_call" ? { block: true, reason } : { warnings: [reason] };
  }
}

/** agent_before_settle 自 Pi 0.87 起可用；版本读不到按不可用处理（回退 followUp）。 */
function hardStopAvailable(): boolean {
  try { return load(ADAPTER).supportsHardStop((host as { VERSION?: string }).VERSION) === true; } catch { return false; }
}

function notify(ctx: any, text: string, level: "warning" | "error"): void {
  try { ctx.ui?.notify?.(text, level); } catch { /* headless */ }
}

export default function (pi: ExtensionAPI) {
  const hardStop = hardStopAvailable();
  let lastStopReason = "";

  pi.on("tool_call", async (event: any, ctx: any) => {
    const out = gate("tool_call", { toolName: event.toolName, input: event.input ?? {} }, ctx.cwd ?? process.cwd());
    if (out.block) return { block: true, reason: out.reason };
  });

  pi.on("tool_result", async (event: any, ctx: any) => {
    gate("tool_result", {
      toolName: event.toolName, input: event.input ?? {}, isError: event.isError,
      exitCode: event.structuredContent?.exit_code ?? event.details?.exitCode,
    }, ctx.cwd ?? process.cwd());
  });

  if (hardStop) {
    // event.context.canContinue 是加入本条 draft 之前的预览（末条为 assistant 时恒为 false），不能拿来挡；
    // draft 是 custom_message（对模型是 user 消息），加入后上下文可续跑，Pi 在提交后自行复核。
    pi.on("agent_before_settle", async (event, ctx) => {
      const out = gate("agent_before_settle", { outcome: event.outcome }, ctx.cwd ?? process.cwd());
      if (out.continue && out.entries?.length) return { entries: [...event.entries, ...out.entries], continue: true };
      for (const w of out.warnings ?? []) if (w.includes("circuit breaker")) notify(ctx, `[athena] ${w}`, "warning");
      return undefined;
    });
  }

  pi.on("agent_end", async (_event: any, ctx: any) => {
    const out = gate("agent_end", { hardStop }, ctx.cwd ?? process.cwd());
    if (!out.stop || !out.reason) { lastStopReason = ""; return; }
    if (out.reason === lastStopReason) {
      notify(ctx, "[athena] 同一 ship 阻断未消解，停止自动纠偏，需人工处理", "warning");
      return;
    }
    lastStopReason = out.reason;
    try {
      pi.sendUserMessage(`[athena · ship 纠偏] ${out.reason}`, { deliverAs: "followUp" });
    } catch {
      notify(ctx, out.reason, "error");
    }
  });
}
