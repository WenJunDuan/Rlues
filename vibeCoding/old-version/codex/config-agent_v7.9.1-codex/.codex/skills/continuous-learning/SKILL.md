---
name: continuous-learning
description: |
  Auto-extract reusable patterns from coding sessions. Activates on session end
  or when /learn command is invoked. Identifies successful patterns, debugging
  solutions, and architectural decisions worth preserving for future sessions.
---

# Continuous Learning Skill

Extract and preserve valuable patterns from development sessions.

## When to Use

- Session ending with significant work completed
- User invokes `/learn` command mid-session
- After successful debugging of complex issues
- When discovering new architectural patterns

## Pattern Categories

| Type | Description |
|:---|:---|
| `code` | Reusable code patterns |
| `debugging` | Debug approaches |
| `architecture` | Design decisions |
| `workflow` | Process improvements |

## Extraction Workflow

1. **Session Analysis** - Evaluate for extractable patterns
2. **Pattern Identification** - Filter reusable, non-trivial solutions
3. **User Confirmation** - Present for approval
4. **Storage** - Save to `.ai_state/experience/learned/`
5. **Index Update** - Add to experience index

## Quality Criteria

Patterns worth extracting must:
- ✅ Be reusable across projects
- ✅ Save significant time/effort
- ✅ Document non-obvious solutions
- ❌ NOT be trivial or well-documented
- ❌ NOT be too project-specific
