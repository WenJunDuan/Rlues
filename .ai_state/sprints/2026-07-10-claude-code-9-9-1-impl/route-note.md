# Route Note — CC Athena 9.9.1 implementation
- Candidates: System full release; P0-only patch.
- Evidence: hooks, ledger, gate, agents, settings, migrate and validation span more than five files.
- Blast radius: cross-module release package; isolated worktree required.
- Reversibility: dedicated branch and worktree from committed CC 9.9.0 baseline.
- Urgency: planned release, not hotfix.
- Uncertainty: acceptance criteria AC1-AC22 are executable.
- Decision: System full release, impl-first with mandatory Fable5 post-review.
- Confidence: 0.99.
- Exit: any shared-schema incompatibility pauses implementation for design revision.
