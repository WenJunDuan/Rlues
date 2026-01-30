---
name: memory
description: |
  Dual-track memory system combining file-based state (.ai_state/) with
  Memory MCP for cross-session persistence. Handles session lifecycle,
  context restoration, and state synchronization.
---

# Memory Skill

## Dual-Track System

### Track 1: File-Based (.ai_state/)
```yaml
Purpose: Project-specific state
Persistence: Git-versioned
Contents:
  - requirements/
  - designs/
  - experience/
  - checkpoints/
  - meta/
```

### Track 2: Memory MCP
```yaml
Purpose: Cross-session memory
Persistence: MCP storage
Contents:
  - User preferences
  - Long-term patterns
  - Project summaries
```

## Session Lifecycle

### Session Start
```yaml
Actions:
  1. Load .ai_state/meta/session.lock
  2. Query Memory MCP for context
  3. Restore last active task
  4. Load relevant experience
```

### Session End
```yaml
Actions:
  1. Save current state to .ai_state/
  2. Update Memory MCP with key insights
  3. Release session.lock
  4. Trigger continuous-learning if needed
```

### Pre-Compact
```yaml
Actions:
  1. Save state to pre-compact-state.yaml
  2. Store key context in Memory MCP
  3. Generate session summary
```

## Memory MCP Integration

```yaml
Store:
  - Key decisions made
  - User preferences
  - Project context summary

Retrieve:
  - Previous session context
  - User interaction patterns
  - Long-term project knowledge
```

## Commands

```bash
/vibe-status         # View current state
/vibe-resume         # Restore from memory
/vibe-pause          # Save and pause
```
