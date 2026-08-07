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
| `.gitignore` | active | Python/secrets/OS ignores, added session 2 |
| `skeleton.py` | active | M2 walking skeleton — hardcoded GitHub+OSV.dev CVE lookup, stdlib-only. Will be refactored behind pluggable interfaces at M7 (DECISION 021), not meant to survive unchanged. |
| `skill_scan.py` | active | M3 skill-mode instruction scan — credential-exfil, instruction-override, shell-pipe-execute red flags, plus fetch-and-follow caveat. Imports from skeleton.py directly (pre-M7, no interface yet). |
| `code_scan.py` | active | M4 repo-mode code red-flag scan — obfuscation, credential-harvesting, suspicious network calls, install-time scripts. Streams file-by-file for memory (not API-call-count, OI-017). |
| `freshness_scan.py` | active | M5 dependency freshness — PyPI+npm lookup, distinguishes pinning style from real staleness. Go not yet supported (OI-018). |
| `verdict.py` | active | M6 severity model + humanized verdict — combines all pillars into traffic-light + narrative, two modes, `--json`. |
| `interfaces.py` | active | M7 — FileAccessProvider (extracted, proven swappable) and ModelProvider (forward-defined for M9) abstract interfaces. |
| `github_provider.py` | active | M7 — GitHubFileAccessProvider, the only v1 file-access implementation, moved verbatim from skeleton.py. |
| `test_provider_swap.py` | active | M7 — proves FileAccessProvider swap works with zero changes to skeleton.py/code_scan.py, using a fake in-memory provider. |
| `repocheck.py` | active | M8 — CLI entry point, zero scan logic, auto-detects repo/skill mode. **V1 complete as of this file.** |

DECISIONS.md now has 22 entries (was 21 at session 1 close — Decision
022 added during the close itself, map was one entry stale, corrected
here).
