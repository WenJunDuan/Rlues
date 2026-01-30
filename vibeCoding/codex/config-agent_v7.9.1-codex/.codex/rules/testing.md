# Testing Rules

## Coverage Requirements

- Minimum 80% code coverage
- 100% coverage for critical paths
- All public APIs must have tests

## Test Structure (AAA)

```typescript
describe('ComponentName', () => {
  describe('methodName', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange - Setup test data
      const input = createTestData();
      
      // Act - Execute the code
      const result = component.method(input);
      
      // Assert - Verify results
      expect(result).toEqual(expected);
    });
  });
});
```

## TDD Workflow

1. **RED** - Write failing test first
2. **GREEN** - Implement minimal code to pass
3. **REFACTOR** - Improve without changing behavior

## Test Types

| Type | Purpose | Location |
|:---|:---|:---|
| Unit | Single function/class | `*.test.ts` |
| Integration | Module interactions | `*.integration.test.ts` |
| E2E | Full user flows | `e2e/*.spec.ts` |

## Anti-Patterns

- NO testing implementation details
- NO flaky tests (random failures)
- NO test interdependence
- NO sleeping in tests (use waitFor)
