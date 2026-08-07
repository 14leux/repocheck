# RepoCheck — Session Instructions

Lightweight subset of `D:\Projects\PROJECT_DISCIPLINE.md` (§10). Follow
§3 (session start) and §4 (session close) from that master file exactly
as written; this file just holds the project-specific entry points and
the Open Items table.

## Boot sequence

1. Read this file in full.
2. Read `tasks/context.md` — branch on Status (CLOSED / INTERRUPTED /
   IN PROGRESS per PROJECT_DISCIPLINE.md §3 step 2).
3. Read `MILESTONES.md` — confirm current session number.
4. Read `tasks/todo.md` — surface `[/]` items.
5. Read `tasks/wip.md` — if not the empty template, crash recovery
   (§5 of the master file).
6. Read relevant sections of `KNOWLEDGE.md` and `DECISIONS.md`.
7. Read `tasks/codebase_map.md` — flag staleness for today's goal.
8. Read the Open Items table below.
9. Write boot summary to `tasks/context.md`, set Status → IN PROGRESS.
10. Declare phase/session/goal, wait for confirmation.

## Close sequence

Follow `PROJECT_DISCIPLINE.md` §4 exactly — KNOWLEDGE.md, DECISIONS.md,
todo.md, this file's Open Items table, MILESTONES.md,
tasks/codebase_map.md, tasks/context.md (+ Close Verification block),
reset tasks/wip.md, commit, push, confirm branch.

## Open Items

| OI | Item | Status | Raised in session |
|----|------|--------|-------------------|
| OI-001 | Confirm "live lookup, not self-mutating local DB" design decision still holds now that real scoping has happened | CLOSED — reconfirmed in session 1, amended (not reversed) by DECISION 006 to allow versioned ruleset releases | 1 |
| OI-002 | Core scan library's language/runtime not yet chosen (needed to support both skill + CLI distribution) | CLOSED — Python chosen, see DECISION 010 | 1 |
| OI-003 | Exact CVE/advisory data sources and their rate limits / auth requirements not yet researched | CLOSED — OSV.dev chosen as primary source, see DECISION 011 | 1 |
| OI-004 | Git-host scope for v1 (GitHub-only vs. also GitLab/Bitbucket) and ecosystem coverage beyond npm/PyPI not yet decided | CLOSED — GitHub-only v1 host behind a pluggable interface, ecosystem breadth via OSV.dev, see DECISION 012 | 1 |
| OI-005 | Verdict/report format not yet designed concretely — needs pre-flight summary state, per-finding explanatory copy, severity triage for long dependency lists | CLOSED — traffic-light + narrative primary, JSON via flag, see DECISION 013 (severity-weighting model itself still owed, tracked under Milestone #6) | 1 |
| OI-006 | CLI's mechanism for accepting/configuring an Anthropic API key for deep-scan mode not yet designed | CLOSED — ANTHROPIC_API_KEY env var only, see DECISION 014 | 1 |
| OI-007 | Exact skill-to-core-library call mechanism not yet decided (script shell-out vs. imported module) | OPEN | 1 |
| OI-008 | Severity-weighting model (how CVSS + red-flag risk + freshness lag combine into one traffic-light signal) not yet designed | OPEN | 1 |
| OI-009 | Instruction-content analysis pattern list for skill mode (DECISION 015) not yet written — needs its own pattern set separate from the code red-flag checklist, and a distinct category for "fetch external URL and follow" (DECISION 020) vs. credential-exfiltration phrasings | OPEN | 1 |
| OI-010 | Skill-mode verdict template (separate from repo-mode template per DECISION 015) not yet designed — needs a distinct "unverifiable-by-scanning" caveat slot per DECISION 020, not just pass/fail findings | OPEN | 1 |
| OI-011 | Deferred from Socratic challenge (`new-project` skill, Step 2), not blocking today: undefined behavior when OSV.dev/GitHub/Anthropic API is down or rate-limited mid-scan (silent skip vs. loud failure vs. partial verdict) | PENDING | 1 |
| OI-012 | Deferred from Socratic challenge, not blocking today: scan-result reproducibility/versioning — no decision on whether a result records which ruleset version / data timestamp it used | PENDING | 1 |
| OI-013 | Deferred from Socratic challenge, not blocking today: false-positive/allowlist mechanism for legitimate patterns that resemble red flags — now has a concrete real example (browser-use SKILL.md's `printf ... \| auth login --api-key-stdin`, a secure secret-handling pattern that a naive "env var + pipe" rule would misflag; see KNOWLEDGE.md) | PENDING | 1 |
| OI-014 | Deferred from Socratic challenge, not blocking today: whether full v1 scope (4 pillars × repo+skill modes × pluggable interfaces × 2 verdict templates) is realistic as one v1 for a solo builder, or is v1+v2 disguised as one milestone list | PENDING | 1 |
| OI-015 | GitHub's hosted code-search API gave unreliable results for a quick pattern sweep during the validation trace — code red-flag pillar should fetch raw file content via the file-access interface (DECISION 012) and pattern-match locally, not depend on a host's search API | OPEN | 1 |
