# Performance Rules

## Model Selection

| Task | Model | Reason |
|:---|:---|:---|
| Quick edits | Default | Fast iteration |
| Complex reasoning | Opus | Better accuracy |
| Long context | Gemini | Extended window |
| Code generation | Codex | Optimized for code |

## Context Window Management

```
Warning Thresholds:
- 50%: Info - Monitor usage
- 70%: Warning - Consider compacting
- 85%: Critical - Compact now
- 95%: Danger - Immediate action
```

## Good Times to Compact

- ✅ After completing a feature
- ✅ Before starting new unrelated work
- ✅ After successful verification
- ✅ At natural conversation breaks

## Bad Times to Compact

- ❌ Mid-debugging session
- ❌ During multi-file refactoring
- ❌ When tracking complex state

## MCP Optimization

- Don't enable all MCPs at once
- Keep under 10 MCPs active per project
- Under 80 tools total
- Use `disabledMcpServers` to disable unused

## Token Optimization

- Prefer skills over verbose prompts
- Load knowledge on-demand
- Use iterative retrieval for large contexts
- Compact state before complex operations
