# tasks/codebase_map.md

| Path | Status | Purpose |
|------|--------|---------|
| `README.md` | active | Project overview, install/usage, glossary — rewritten for real usage at M12 |
| `CLAUDE.md` | active | Agent entry point, non-negotiables (4) |
| `CONTRIBUTING.md` | active | M12 — red-flag-rule contribution process per DECISIONS.md #006 |
| `LICENSE` | active | MIT license (DECISIONS.md #005) |
| `.gitignore` | active | Python/secrets/OS ignores |
| `.agent/instructions.md` | active | Boot/close sequence, Open Items table (OI-001–OI-021) |
| `DECISIONS.md` | active | Decision log — 23 entries |
| `MILESTONES.md` | active | 12 milestones, all DONE (M9 partial — OI-020 open) |
| `KNOWLEDGE.md` | active | Confirmed learnings — validation traces, 2 rounds of independent QA, all post-M12 open-item fixes |
| `council-transcript-20260807T000000.md` | active | 8-advisor llm-council run on v1 scope (session 1) |
| `tasks/context.md` | active | Live session checkpoint |
| `tasks/wip.md` | active | Crash-recovery pad |
| `tasks/todo.md` | active | Task board |
| `tasks/codebase_map.md` | active | This file |
| `skeleton.py` | active | Core: CVE lookup via OSV.dev, manifest parsing (PyPI/npm/Go), `parse_repo_arg` (hardened against malformed input), `resolve_package_versions` (npm caret/tilde resolution), `strip_invisible_characters` (shared Unicode-evasion fix), module-level `list_tree`/`fetch_file`/`fetch_all_files` delegating to the active `FileAccessProvider` |
| `skill_scan.py` | active | Skill-mode instruction scan — credential-exfil (incl. env-var-shaped secrets), instruction-override (broadened guard), shell-pipe-execute (incl. xargs/download-then-execute), fetch-and-follow caveat |
| `code_scan.py` | active | Repo-mode code red-flag scan — obfuscation (co-occurrence-gated), credential-harvesting (multi-language/library), suspicious network calls (private-IP-excluded), install-time scripts. Scans `.ps1` too |
| `freshness_scan.py` | active | Dependency freshness — PyPI, npm, and Go (case-encoded module proxy), concurrent lookups |
| `verdict.py` | active | Severity model + humanized verdict — both modes, `--json`, degraded-state handling, suppression, reproducibility metadata, concurrent + bulk-fetch pillars |
| `interfaces.py` | active | `FileAccessProvider` (extracted, proven swappable, `fetch_all_files` bulk-fetch method) and `ModelProvider` (forward-defined for M9) |
| `github_provider.py` | active | `GitHubFileAccessProvider` — per-file contents API plus `fetch_all_files` (one tarball download, graceful per-file fallback verified with a real simulated failure) |
| `semver_resolve.py` | active | npm caret/tilde range resolution against the live registry, no third-party semver lib |
| `suppression.py` | active | `.repocheck-allow.json` suppression mechanism, category+path matching, type-validated |
| `concurrency.py` | active | Shared thread-pool helper (`parallel_map`), ~9x measured speedup, used by verdict.py/freshness_scan.py/skeleton.py |
| `test_provider_swap.py` | active | Proves `FileAccessProvider` swap works with zero changes to calling code, using a fake in-memory provider |
| `repocheck.py` | active | CLI entry point — zero scan logic, auto-detects repo/skill mode, exits non-zero on a failed/degraded scan |
| `anthropic_provider.py` | active | `AnthropicModelProvider` — raw HTTP (no SDK dep), specific missing-key error |
| `deep_scan.py` | active | Opt-in deep scan — high-risk file selection, prompt-injection-safe prompt, `--confirm` required. NOT yet verified against a live API call (OI-020) |
| `verify_deep_scan.py` | active | Live-verification script for deep_scan.py's 2 unverified acceptance criteria (OI-020) — run once `ANTHROPIC_API_KEY` is available |
| `skills/repocheck/SKILL.md` | active | RepoCheck's own Claude Code skill wrapper — scans clean under its own instruction-scan (dogfooding found and fixed a real false positive) |

**ALL 12 MILESTONES COMPLETE.** Repo is public at
github.com/14leux/repocheck, default branch `main`. Only tracked open
items remain: OI-020 (blocked on a live `ANTHROPIC_API_KEY`, not this
session's to resolve) and OI-021 (proximity-based obfuscation matching,
needs AST-level analysis — deferred, larger scope than a pattern fix).

**Reconcile note (this close):** `git ls-files` compared against this
map — all 30 tracked files accounted for, no mapped-but-deleted
entries. Fixed two staleness issues found during reconcile: a broken
markdown table (a stray blank line had split it into two separate
tables) and three descriptions that still described pre-fix state
(`code_scan.py`/`freshness_scan.py` referencing OI-017/OI-018 as open
when both are now closed). Also consolidated three function-level rows
that had been added ad hoc (`skeleton.strip_invisible_characters()`,
`freshness_scan.go_freshness()`, `github_provider.fetch_all_files()`)
back into their parent file's single row — the map's granularity is
files, not functions within already-mapped files.
