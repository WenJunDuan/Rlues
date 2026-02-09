# Agent Delegation Rules

## When to Delegate

| Scenario | Delegate To |
|:---|:---|
| Implementation planning | planner |
| Architecture decisions | architect |
| Code quality review | code-reviewer |
| Security concerns | security-reviewer |
| Build errors | build-error-resolver |
| E2E test creation | e2e-runner |

## Delegation Protocol

1. **Context Handoff** - Provide relevant files and state
2. **Clear Objective** - Specific deliverable expected
3. **Scope Limits** - What agent should NOT do
4. **Return Criteria** - When to return control

## Subagent Limits

- Max tools: Limit to required tools only
- Max files: Scope to relevant files
- No cascading: Subagents should not spawn subagents

## Context Management

Use `context: fork` for:
- Experimental changes
- Isolated analysis
- Parallel exploration

## Anti-Patterns

- DON'T delegate simple tasks
- DON'T delegate without context
- DON'T let subagents modify critical files
- DON'T run multiple subagents on same files
