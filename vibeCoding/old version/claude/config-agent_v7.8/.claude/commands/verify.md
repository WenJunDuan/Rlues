---
name: verify
description: |
  Run verification loop to ensure code quality. Executes tests, linting,
  type checking, and security scans. Reports issues and blocks progress
  until critical issues are resolved. Use before commits and deployments.
---

# /verify - Run Verification Loop

## Usage

```bash
/verify                    # Full verification
/verify --focus=tests      # Tests only
/verify --focus=lint       # Linting only
/verify --focus=security   # Security scan
/verify --quick            # Fast checks only
/verify --final            # Pre-commit gate
```

## Verification Suite

### Code Quality
- [ ] TypeScript strict mode
- [ ] ESLint/Prettier clean
- [ ] No `any` types
- [ ] Error handling complete

### Testing
- [ ] Unit tests pass
- [ ] Coverage >= 80%
- [ ] Integration tests pass
- [ ] Edge cases covered

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] Dependencies secure
- [ ] No SQL injection

### Performance
- [ ] No N+1 queries
- [ ] Bundle size acceptable
- [ ] No memory leaks

## Verification Flow

```
┌─────────────────────────┐
│ 1. Run Test Suite       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 2. Run Linters          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 3. Check Coverage       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ 4. Security Scan        │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌───────┐     ┌─────────┐
│ PASS  │     │  FAIL   │
└───────┘     └────┬────┘
                   │
                   ▼
            [Fix & Retry]
```

## Report Format

```markdown
# Verification Report

## Summary
Status: ✅ PASS / ❌ FAIL
Duration: 45s

## Code Quality
- TypeScript: ✅ No errors
- Lint: ✅ Clean
- Format: ✅ Consistent

## Tests
- Unit: 42/42 passing
- Coverage: 87%

## Security
- Secrets: ✅ Clean
- Deps: ⚠️ 2 low vulnerabilities

## Issues
1. [LOW] Unused import auth.ts:15

## Recommendation
✅ Ready to proceed
```

## Exit Codes

| Code | Meaning |
|:---|:---|
| 0 | All checks pass |
| 1 | Tests failed |
| 2 | Lint errors |
| 3 | Security issues |
| 4 | Coverage below threshold |

## Integration

Works with:
- `verification-loop` skill for detailed checks
- `checkpoint` command for state snapshots
- CI/CD pipelines

## Example

```bash
$ /verify --final

🔍 Running verification...

Tests:     ✅ 42/42 passing (12s)
Lint:      ✅ Clean
TypeScript: ✅ No errors  
Coverage:  ✅ 87% (threshold: 80%)
Security:  ⚠️ 2 low severity

Overall: ✅ PASS

Ready to commit!
```
