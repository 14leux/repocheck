# tasks/codebase_map.md

| Path | Status | Purpose |
|------|--------|---------|
| `README.md` | active | Project overview, origin, status of scoping decisions |
| `CLAUDE.md` | active | Agent entry point, non-negotiables (4) |
| `LICENSE` | active | MIT license (DECISIONS.md #005) |
| `.agent/instructions.md` | active | Boot/close sequence, Open Items table (OI-001–OI-015) |
| `DECISIONS.md` | active | Decision log — 21 entries |
| `MILESTONES.md` | active | 12 milestones, grouped V1 / Hardening / Release |
| `KNOWLEDGE.md` | active | Confirmed learnings — session 1 validation trace findings |
| `council-transcript-20260807T000000.md` | active | 8-advisor llm-council run on v1 scope (session 1) |
| `tasks/context.md` | active | Live session checkpoint |
| `tasks/wip.md` | active | Crash-recovery pad |
| `tasks/todo.md` | active | Task board |
| `tasks/codebase_map.md` | active | This file |

No source code exists yet. M2 (walking skeleton) is the first milestone
that creates any — see MILESTONES.md.

**Reconcile note (session 1 close):** `git ls-files` compared against
this map. Two entries were missing and have been added — `LICENSE` and
`council-transcript-20260807T000000.md`. No mapped-but-deleted entries.
`.gitignore` does not exist yet — planned for session 2 before the first
code commit (tasks/todo.md).
