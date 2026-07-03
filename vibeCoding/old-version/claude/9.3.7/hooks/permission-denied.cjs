// VibeCoding v9.3.7 — PermissionDenied: 不重试, 换策略
// 官方格式: hookSpecificOutput.hookEventName + retry
process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: "PermissionDenied",
    retry: false
  }
}));
process.exit(0);
