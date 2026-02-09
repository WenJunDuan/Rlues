---
name: iterative-retrieval
description: |
  Progressive context refinement for subagents and complex tasks. Retrieves
  context incrementally based on actual needs rather than loading everything
  upfront. Reduces context waste and improves relevance.
context: fork
---

# Iterative Retrieval Skill

## Problem

Loading all potentially relevant context upfront:
- Wastes context window
- Includes irrelevant information
- Reduces signal-to-noise ratio

## Solution

Retrieve context incrementally based on actual execution needs.

## Retrieval Levels

```
Level 0: Task Description
  └── Just the user request

Level 1: Immediate Context
  └── Files mentioned + direct dependencies

Level 2: Extended Context
  └── Related modules + tests

Level 3: Full Context
  └── Architecture docs + cross-cutting concerns
```

## Retrieval Protocol

### 1. Start Minimal
```yaml
initial_load:
  - Task description
  - CLAUDE.md (current section)
  - Target file(s) only
```

### 2. Detect Gaps
```yaml
gap_signals:
  - Reference to unknown function/type
  - Import from unloaded module
  - Pattern that needs clarification
  - Test failure with unclear cause
```

### 3. Retrieve On-Demand
```yaml
retrieval_action:
  signal: "Unknown type UserProfile"
  action: Load types/user.ts
  scope: Type definitions only
```

### 4. Cache Decisions
```yaml
cache_entry:
  query: "UserProfile type"
  result: "types/user.ts lines 15-30"
  relevance: 0.95
  reuse_for: ["user-related tasks"]
```

## Implementation Patterns

### For Subagent Delegation

```markdown
# Subagent Context Protocol

## Mandatory (Level 0-1)
- Task objective
- Target file
- Immediate imports

## On-Request (Level 2)
- Related tests
- Usage examples
- Similar implementations

## Escalation (Level 3)
- Architecture docs
- Cross-module dependencies
- Historical decisions
```

### For Complex Analysis

```javascript
async function iterativeAnalysis(task) {
  // Level 0: Understand task
  const taskContext = await loadMinimal(task);
  
  // Level 1: Load immediate
  let context = await loadImmediate(task.files);
  
  while (hasGaps(context)) {
    // Level 2+: Fill gaps
    const gaps = identifyGaps(context);
    const additional = await loadForGaps(gaps);
    context = mergeContext(context, additional);
    
    // Prevent infinite loops
    if (context.level > MAX_LEVEL) break;
  }
  
  return context;
}
```

## Gap Detection Rules

| Signal | Action | Priority |
|:---|:---|:---|
| Undefined reference | Load definition file | High |
| Test import | Load test file | Medium |
| Config reference | Load config | Medium |
| Doc comment link | Load doc | Low |
| Historical mention | Query experience | Low |

## Context Scoring

```yaml
relevance_score:
  direct_reference: 1.0    # Explicitly mentioned
  import_chain: 0.8        # Imported by target
  type_dependency: 0.7     # Type used
  test_coverage: 0.6       # Tests target
  same_module: 0.5         # Same directory
  doc_reference: 0.4       # Documentation
  historical: 0.3          # Past experience
```

## Integration with VibeCoding

### With phase-router
```yaml
routing_context:
  path_a: level 0-1 only
  path_b: level 0-2
  path_c: full iterative
```

### With subagents
```yaml
subagent_protocol:
  initial: level 0-1
  on_request: level 2
  escalate_to_main: level 3
```

### With verification-loop
```yaml
verification_context:
  initial: test file + target
  on_failure: add related modules
  on_complex_failure: full context
```

## Anti-Patterns

❌ **Don't**: Load entire codebase upfront
✅ **Do**: Start with target file only

❌ **Don't**: Include all tests
✅ **Do**: Load tests when verification fails

❌ **Don't**: Pass full history to subagent
✅ **Do**: Pass task-relevant summary

❌ **Don't**: Keep irrelevant context
✅ **Do**: Prune after task completion

## Metrics

Track retrieval efficiency:
```yaml
session_metrics:
  initial_context_tokens: 2000
  final_context_tokens: 8000
  retrieval_requests: 5
  cache_hits: 3
  relevance_score_avg: 0.82
```
