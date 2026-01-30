---
name: checkpoint
description: |
  Save verification checkpoint for current work state. Captures files modified,
  test status, and context for later restoration or comparison. Essential for
  complex multi-step implementations and before risky changes.
---

# /checkpoint - Save Verification State

## Usage

```bash
/checkpoint "auth-complete"      # Create named checkpoint
/checkpoint --list               # List all checkpoints
/checkpoint --restore "name"     # Restore checkpoint
/checkpoint --diff "a" "b"       # Compare checkpoints
/checkpoint --delete "name"      # Delete checkpoint
```

## Checkpoint Contents

```yaml
Checkpoint:
  name: auth-complete
  timestamp: 2025-01-23T15:00:00Z
  files_modified:
    - src/middleware.ts
    - src/lib/auth.ts
  tests_status: passing
  lint_status: clean
  coverage: 85%
  git_state:
    branch: feature/auth
    commit: abc1234
  notes: "JWT validation implemented"
  context:
    - Using RS256 for signing
    - Token in httpOnly cookie
```

## Storage

```
.ai_state/checkpoints/
├── checkpoint-001-auth-complete.yaml
├── checkpoint-002-api-routes.yaml
└── checkpoint-latest.yaml
```

## Commands

### Create
```bash
/checkpoint "feature-name"
# Creates timestamped checkpoint with current state
```

### List
```bash
/checkpoint --list
# Shows all checkpoints with summary
```

### Restore
```bash
/checkpoint --restore "auth-complete"
# Loads checkpoint context (does NOT restore files)
# Use git for actual file restoration
```

### Compare
```bash
/checkpoint --diff "checkpoint-1" "checkpoint-2"
# Shows differences between checkpoints
```

## Integration

Works with:
- `verification-loop` skill for quality gates
- `strategic-compact` skill for state preservation
- Git for actual file versioning

## Example Output

```
✅ Checkpoint created: auth-complete

Files tracked: 5
Tests: 42/42 passing
Coverage: 87%
Lint: Clean

Location: .ai_state/checkpoints/checkpoint-003-auth-complete.yaml

Tip: Use /verify before major changes
```
