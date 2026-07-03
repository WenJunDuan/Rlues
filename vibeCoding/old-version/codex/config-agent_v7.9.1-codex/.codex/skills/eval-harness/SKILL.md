---
name: eval-harness
description: |
  Verification loop evaluation framework. Provides graders, metrics, and
  pass@k evaluation for code quality assurance. Integrates with verification-loop
  for systematic quality gates.
---

# Eval Harness Skill

## Overview

Systematic evaluation framework for verification loops with:
- Multiple grader types
- Pass@k metrics
- Quality gates
- Regression detection

## Grader Types

### 1. Exact Match Grader
```yaml
grader: exact_match
config:
  case_sensitive: false
  trim_whitespace: true
  
example:
  expected: "Hello World"
  actual: "hello world"
  result: PASS (case insensitive)
```

### 2. Contains Grader
```yaml
grader: contains
config:
  required: ["function", "return", "export"]
  forbidden: ["console.log", "debugger", "any"]
  
example:
  code: "export function add(a, b) { return a + b; }"
  result: PASS (has required, no forbidden)
```

### 3. AST Grader
```yaml
grader: ast
config:
  language: typescript
  rules:
    - no_any_types
    - has_return_type
    - max_complexity: 10
    
example:
  code: "function add(a: number, b: number): number { return a + b; }"
  result: PASS
```

### 4. Test Runner Grader
```yaml
grader: test_runner
config:
  command: "npm test"
  coverage_threshold: 80
  timeout: 60s
  
example:
  tests_passed: 45/45
  coverage: 85%
  result: PASS
```

### 5. LLM Grader
```yaml
grader: llm
config:
  model: claude-sonnet
  criteria:
    - code_quality
    - follows_requirements
    - no_security_issues
  threshold: 0.8
  
example:
  scores: [0.9, 0.85, 0.95]
  average: 0.9
  result: PASS
```

## Pass@k Evaluation

Generate k samples and check if any pass:

```yaml
pass_at_k:
  k: 3
  strategy: best_of_k
  
  samples:
    - attempt_1: FAIL (test error)
    - attempt_2: PASS
    - attempt_3: PASS
  
  result: PASS (2/3 passed)
  pass@1: 0.67
  pass@3: 1.0
```

## Quality Gates

### Gate Configuration
```yaml
quality_gates:
  pre_commit:
    graders: [contains, test_runner]
    threshold: all_pass
    blocking: true
    
  pre_review:
    graders: [ast, llm]
    threshold: 0.8
    blocking: false
    
  pre_release:
    graders: [test_runner, security_scan]
    threshold: all_pass
    blocking: true
```

### Gate Execution
```bash
/verify --gate=pre_commit

Results:
  ✅ contains: PASS (no forbidden patterns)
  ✅ test_runner: PASS (100% tests, 85% coverage)
  
Gate Status: PASS
```

## Checkpoint Evaluation

Compare against saved checkpoints:

```yaml
checkpoint_eval:
  baseline: checkpoint-001
  current: HEAD
  
  metrics:
    tests_delta: +5 (45 → 50)
    coverage_delta: +3% (82% → 85%)
    complexity_delta: -2 (avg 8 → 6)
    
  regression_check:
    new_failures: 0
    removed_tests: 0
    
  result: IMPROVEMENT
```

## Metrics Dashboard

```
📊 Evaluation Summary

Session: 2026-01-28
Evaluations: 12
Pass Rate: 83%

By Grader:
  exact_match:  10/10 (100%)
  contains:     11/12 (92%)
  test_runner:  9/12 (75%)
  ast:          10/12 (83%)

Trends:
  ↑ Coverage: 78% → 85%
  ↓ Complexity: 12 → 8
  → Test count: 45 stable
```

## Integration

### With verification-loop
```yaml
verification_loop:
  on_execute:
    - run: eval-harness
    - graders: [test_runner, contains]
    
  on_checkpoint:
    - run: eval-harness
    - graders: [ast, llm]
    - save_metrics: true
    
  on_final:
    - run: eval-harness
    - graders: all
    - gate: pre_release
```

### With continuous-learning-v2
```yaml
learning_from_evals:
  on_repeated_failure:
    - capture_instinct: true
    - pattern: "failure reason"
    - solution: "how it was fixed"
    
  on_consistent_pass:
    - boost_confidence: true
    - related_instincts: [tag match]
```

## Custom Graders

Create project-specific graders:

```javascript
// .ai_state/graders/api-response.js
module.exports = {
  name: 'api_response',
  evaluate: async (code) => {
    const hasErrorHandling = /catch|try/.test(code);
    const hasTypedResponse = /Response</.test(code);
    
    return {
      pass: hasErrorHandling && hasTypedResponse,
      score: (hasErrorHandling ? 0.5 : 0) + (hasTypedResponse ? 0.5 : 0),
      details: { hasErrorHandling, hasTypedResponse }
    };
  }
};
```

## Anti-Patterns

❌ Single grader for all checks
✅ Appropriate grader per concern

❌ Binary pass/fail only
✅ Scored results with thresholds

❌ Skip evals on "simple" changes
✅ Consistent evaluation always

❌ Ignore eval trends
✅ Track and act on regressions
