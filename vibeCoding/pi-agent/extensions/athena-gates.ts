/**
 * Athena v9.9.6 · pi 端门禁适配器 (Phase-2)
 *
 * 设计: 不重写 CC 端已验证的门禁逻辑 — cc-core/*.cjs 原样复用 (与 claude/9.9.6 同源),
 * 本文件只做协议转换:
 *   pi tool_call (bash)        → pre-bash-guard.cjs  PreToolUse payload → exit 2 = block
 *   pi tool_call (edit/write)  → delivery-gate.cjs   PreToolUse payload → {decision:"block"} = block
 *   pi agent_end               → delivery-gate.cjs   Stop payload       → followUp 纠偏消息
 *
 * 已知语义降级 (MIGRATION.md): pi 无硬 Stop block — Stop 门禁降级为 followUp 纠偏,
 * 同一 reason 不重复发 (防 agent_end 循环轰炸), 改用 ui.notify。
 * 错误语义对齐 CC 平台: hook 自身崩溃/超时 → 放行 (仅显式 block 才拦), 与 CC hook 超时行为一致。
 */
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const CORE = path.join(path.dirname(fileURLToPath(import.meta.url)), "cc-core");
const GATED_WRITE_TOOLS = new Set(["edit", "write", "multiedit", "apply_patch"]);

interface HookResult { code: number; stdout: string; stderr: string; failed: boolean }

function runHook(script: string, payload: unknown, timeoutMs: number, cwd: string): HookResult {
  try {
    const stdout = execFileSync(process.execPath, [path.join(CORE, script)], {
      input: JSON.stringify(payload),
      encoding: "utf8",
      timeout: timeoutMs,
      cwd,
    });
    return { code: 0, stdout, stderr: "", failed: false };
  } catch (err: any) {
    if (typeof err?.status === "number") {
      return { code: err.status, stdout: String(err.stdout ?? ""), stderr: String(err.stderr ?? ""), failed: false };
    }
    // spawn 失败 / 超时: 对齐 CC 平台超时语义 = 放行 (failed 标记供调用方提示)
    return { code: 0, stdout: "", stderr: String(err?.message ?? err), failed: true };
  }
}

function blockDecision(result: HookResult): string | null {
  if (result.code === 2) return result.stderr.trim() || "blocked by gate (exit 2)";
  for (const line of result.stdout.split("\n")) {
    const t = line.trim();
    if (!t.startsWith("{")) continue;
    try {
      const parsed = JSON.parse(t);
      if (parsed?.decision === "block") return String(parsed.reason ?? "blocked by delivery-gate");
    } catch { /* 非 JSON 行忽略 */ }
  }
  return null;
}

export default function (pi: ExtensionAPI) {
  let lastStopReason = "";

  pi.on("tool_call", async (event: any, ctx: any) => {
    const tool = String(event.toolName ?? "").toLowerCase();
    const cwd = ctx.cwd ?? process.cwd();

    if (tool === "bash") {
      const result = runHook("pre-bash-guard.cjs", {
        hook_event_name: "PreToolUse",
        tool_name: "Bash",
        tool_input: { command: String(event.input?.command ?? "") },
        cwd,
      }, 5000, cwd);
      const reason = blockDecision(result);
      if (reason) return { block: true, reason: `[pre-bash-guard] ${reason.replace(/^\[pre-bash-guard\]\s*/, "")}` };
      return;
    }

    if (GATED_WRITE_TOOLS.has(tool)) {
      const result = runHook("delivery-gate.cjs", {
        hook_event_name: "PreToolUse",
        tool_name: tool,
        tool_input: event.input ?? {},
        cwd,
      }, 15000, cwd);
      const reason = blockDecision(result);
      if (reason) return { block: true, reason };
    }
  });

  pi.on("agent_end", async (_event: any, ctx: any) => {
    const cwd = ctx.cwd ?? process.cwd();
    const result = runHook("delivery-gate.cjs", { hook_event_name: "Stop", cwd }, 60000, cwd);
    const reason = blockDecision(result);
    if (!reason) { lastStopReason = ""; return; }
    if (reason === lastStopReason) {
      // 同一阻断重复出现: 不再追加消息 (对应 CC 端熔断器意图), 仅提示人类
      try { ctx.ui?.notify?.("[delivery-gate] 同一阻断未消解, 停止自动纠偏, 需人工处理", "warning"); } catch { /* headless */ }
      return;
    }
    lastStopReason = reason;
    try {
      pi.sendUserMessage(`[delivery-gate · Stop 纠偏] ${reason}`, { deliverAs: "followUp" });
    } catch {
      try { ctx.ui?.notify?.(`[delivery-gate] ${reason}`, "error"); } catch { /* headless */ }
    }
  });
}
