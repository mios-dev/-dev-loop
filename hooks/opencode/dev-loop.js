/**
 * dev-loop plugin for OpenCode.
 *
 * OpenCode is the outlier among the harnesses this repo serves: it has NO
 * declarative hook file. Lifecycle extension is a JS/TS module that exports an
 * async plugin function returning event handlers. Writing an `.opencode/hooks.json`
 * here would be the exact defect the dev-loop exists to catch -- it would look
 * installed and do nothing.
 *
 * This module shells out to the same `hooks/*.sh` scripts every other harness
 * uses. Those scripts speak Claude Code's contract (JSON in, `hookSpecificOutput`
 * out), so no separate adapter process is needed: this file builds the payload and
 * reads the verdict itself.
 *
 * DEVLOOP_HOOKS below is rewritten to an absolute path by ../register-hooks.sh at
 * install time, because unlike the JSON manifests this file is COPIED into the
 * plugins directory rather than referenced in place.
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const DEVLOOP_HOOKS = "${DEVLOOP_HOOKS}";
const TIMEOUT_MS = 20000;

/** Run a dev-loop hook script with a Claude-shaped payload; return parsed stdout or null. */
function runHook(script, payload) {
  const path = DEVLOOP_HOOKS + "/" + script;
  if (!existsSync(path)) {
    console.error("dev-loop: missing hook script " + path);
    return null;
  }
  const res = spawnSync("sh", [path], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: TIMEOUT_MS,
  });
  if (res.error) {
    // Never let the guard wedge a session: log and allow.
    console.error("dev-loop: " + script + " failed: " + res.error.message);
    return null;
  }
  if (res.stderr) console.error(res.stderr);
  const out = (res.stdout || "").trim();
  if (!out) return null;
  try {
    return JSON.parse(out);
  } catch {
    return null;
  }
}

/** Claude-shaped deny -> reason string, or null. */
function denyReason(result) {
  const h = result && result.hookSpecificOutput;
  if (h && h.permissionDecision === "deny") {
    return h.permissionDecisionReason || "denied by dev-loop";
  }
  return null;
}

export const DevLoopPlugin = async ({ directory }) => {
  return {
    /**
     * Gate every tool call. Routing is by the SHAPE of output.args, not by tool
     * name: a command-bearing call goes to guard.sh, a path-bearing call goes to
     * no-env.sh. Throwing aborts the call -- that is OpenCode's documented refusal.
     */
    "tool.execute.before": async (input, output) => {
      const args = (output && output.args) || {};
      const command = typeof args.command === "string" ? args.command : "";
      const filePath =
        (typeof args.filePath === "string" && args.filePath) ||
        (typeof args.file_path === "string" && args.file_path) ||
        (typeof args.path === "string" && args.path) ||
        "";

      if (command) {
        const reason = denyReason(runHook("guard.sh", { tool_input: { command } }));
        if (reason) throw new Error(reason);
      }
      if (filePath) {
        const reason = denyReason(
          runHook("no-env.sh", { tool_input: { file_path: filePath } }),
        );
        if (reason) throw new Error(reason);
      }
    },
  };
};

export default DevLoopPlugin;
