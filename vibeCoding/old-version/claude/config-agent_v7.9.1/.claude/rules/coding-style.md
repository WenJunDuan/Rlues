# Coding Style Rules

## Core Principles

1. **Immutability First** - Prefer const, readonly, immutable data structures
2. **Small Functions** - Max 50 lines per function
3. **Single Responsibility** - One function = one purpose
4. **Early Return** - Exit early to reduce nesting

## Naming Conventions

```
Variables: camelCase (descriptive, no abbreviations)
Functions: camelCase (verb + noun)
Classes: PascalCase
Constants: UPPER_SNAKE_CASE
Files: kebab-case.ts
```

## TypeScript Specific

- NO `any` types - use `unknown` or proper typing
- Enable strict mode
- Define interfaces before implementation
- Export types separately from implementations

## File Organization

```
Max 300 lines per file
Group imports: external → internal → relative
One component per file (React)
Colocate tests with source files
```

## Comments

- Code should be self-documenting
- Comments explain WHY, not WHAT
- JSDoc for public APIs only
- Remove commented-out code
