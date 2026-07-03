# Session Lifecycle Hooks

## OnSessionStart
```yaml
actions:
  - Load .ai_state/meta/session.lock
  - Query Memory MCP
  - Restore last context
  - Check pending tasks
```

## OnSessionEnd
```yaml
actions:
  - Save state to .ai_state/
  - Update Memory MCP
  - Trigger continuous-learning
  - Release session.lock
```

## PreCompact
```yaml
actions:
  - Save pre-compact-state.yaml
  - Store key context
  - Generate summary
```

## PostCompact
```yaml
actions:
  - Load saved state
  - Restore context
  - Continue work
```
