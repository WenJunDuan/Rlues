# VibeCoding Kernel v7.8 for Codex

> **"Talk is cheap. Show me the code."** — Linus Torvalds

## Working Agreements

### Seven Rules (七条铁律)

1. **Read Before Write** - Always read target files before modifying
2. **Knowledge First** - Query knowledge base and experience before development
3. **Cunzhi Pause** - Pause at critical decision points for human confirmation
4. **State Sync** - Update .ai_state/ after any changes
5. **Verification Loop** - Verify results after execution
6. **Experience Deposit** - Deposit learnings to experience library after completion
7. **Capability Enhancement** - Prefer MCP tools and Skills

### Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  User Layer       User Input / $vibe-dev "new feature"          │
├─────────────────────────────────────────────────────────────────┤
│  Skill Layer      $context7 / $knowledge-base / $experience     │
├─────────────────────────────────────────────────────────────────┤
│  Agent Layer      phase-router → Functional Agents              │
│                   requirement-mgr / design-mgr / impl-executor  │
├─────────────────────────────────────────────────────────────────┤
│  Workflow Layer   RIPER / P.A.C.E. / Nine-Steps                 │
├─────────────────────────────────────────────────────────────────┤
│  Storage Layer    .ai_state/ + .knowledge/                      │
└─────────────────────────────────────────────────────────────────┘
```

## Intent Routing (phase-router)

```yaml
Routing Rules:
  No task ID → New task (requirement creation)
  Task ID + "change/modify" → Change management
  Task ID + "design/architecture" → Solution design
  Task ID + "develop/implement" → Development execution
  Task ID + "complete/release" → Archive and release
  Task ID only → Infer current state and continue
```

## Nine-Step Workflow

| Step | Phase | Cunzhi Point |
|:---|:---|:---|
| 1 | Requirement Creation | - |
| 2 | Requirement Review | `[REQ_READY]` |
| 3 | Solution Design | - |
| 4 | Design Review | `[DESIGN_READY]` |
| 5 | Environment Setup | - |
| 6 | Development | `[PHASE_DONE]` |
| 7 | Code Commit | - |
| 8 | Release | `[RELEASE_READY]` |
| 9 | Archive | `[TASK_DONE]` |

## P.A.C.E. Complexity Router

| Path | Criteria | Workflow | Duration |
|:---|:---|:---|:---|
| A | Single file, <30 lines | R1→E→R2 | 30-60 min |
| B | 2-10 files | R1→I→P→E→R2 | 2-8 hours |
| C | >10 files, cross-module | Full nine-steps | Days+ |

## Skills Reference

Invoke skills with `$skill-name` syntax:

| Skill | Purpose |
|:---|:---|
| `$context7` | Fetch up-to-date library documentation |
| `$knowledge-base` | Query project knowledge |
| `$experience` | Search and deposit experience |
| `$verification-loop` | Run verification checks |
| `$continuous-learning` | Extract reusable patterns |
| `$strategic-compact` | Context optimization |
| `$phase-router` | Intent recognition and routing |
| `$riper` | RIPER workflow execution |
| `$cunzhi` | Pause protocol |
| `$code-quality` | Quality checks |

## Data Storage

```
.ai_state/
├── requirements/     # Requirement docs (REQ-xxx.md)
├── designs/          # Design docs (DESIGN-xxx.md)
├── experience/       # Experience library
│   └── learned/      # Auto-extracted patterns
├── checkpoints/      # Verification checkpoints
└── meta/             # Session state, kanban

.knowledge/           # External knowledge base
├── project/          # Project docs
├── standards/        # Dev standards
└── tech/             # Tech stack docs
```

## Cunzhi Protocol (寸止)

At critical points, pause and wait for human confirmation:

```
---
🛑 **[PLAN_READY]** Cunzhi - Awaiting Confirmation

Please review the above plan:
- `continue` - Execute plan
- `modify` - Adjust and re-plan
- `cancel` - Abort task
---
```

## Quality Checklist (Linus Style)

- [ ] **Data First**: Is the data structure minimal?
- [ ] **Naming**: Does naming reflect essence?
- [ ] **Simplicity**: Over-engineered? What can be removed?
- [ ] **Taste**: Does the code have "good taste"?
- [ ] **No Any**: No TypeScript `any` types
- [ ] **Error Handling**: Complete error handling?

---
**Version**: v7.8.0 | **Architecture**: VibeCoding Modular | **For**: Codex CLI
