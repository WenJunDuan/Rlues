---
name: strategic-compact
description: |
  Intelligent context window management with strategic compaction suggestions.
  Monitors context usage and suggests /compact at logical boundaries. Saves
  state before compaction to enable recovery.
---

# Strategic Compact Skill

Optimize context window usage through intelligent compaction timing.

## Warning Thresholds

| Level | Usage | Action |
|:---|:---|:---|
| Info | 50% | Monitor |
| Warning | 70% | Suggest compact soon |
| Critical | 85% | Urgent compaction needed |
| Danger | 95% | Immediate compaction |

## Good Times to Compact
- ✅ After completing a feature/task
- ✅ Before starting new unrelated work
- ✅ After successful verification
- ✅ At natural conversation breaks

## Bad Times to Compact
- ❌ Mid-debugging session
- ❌ During multi-file refactoring
- ❌ When tracking complex state

## Pre-Compaction Workflow

1. **State Capture** - Save current task context
2. **Save State** - Write to pre-compact-state.yaml
3. **Generate Summary** - Create session summary
4. **Execute Compaction** - /compact --preserve-state

## Post-Compaction Recovery

```bash
/resume --from-compact
```

Loads pre-compact-state.yaml and restores context.
