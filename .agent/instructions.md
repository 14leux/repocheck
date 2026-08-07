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
| OI-007 | Exact skill-to-core-library call mechanism not yet decided (script shell-out vs. imported module) | CLOSED — SKILL.md itself is the wrapper, shells out to repocheck.py via Bash; see DECISION 023 | 1 |
| OI-008 | Severity-weighting model (how CVSS + red-flag risk + freshness lag combine into one traffic-light signal) not yet designed | CLOSED — implemented in verdict.py (M6): weighted critical/high/moderate/low, aggregate takes the MAXIMUM never an average | 1 |
| OI-009 | Instruction-content analysis pattern list for skill mode (DECISION 015) not yet written — needs its own pattern set separate from the code red-flag checklist, and a distinct category for "fetch external URL and follow" (DECISION 020) vs. credential-exfiltration phrasings | CLOSED — implemented in skill_scan.py (M3): FETCH_AND_FOLLOW_PATTERN reported as its own `dynamic-external-content` caveat, structurally separate from the credential-exfiltration/instruction-override/shell-pipe-execute finding categories. Resolved during implementation, not marked closed until this session-close reconcile caught the gap | 1 |
| OI-010 | Skill-mode verdict template (separate from repo-mode template per DECISION 015) not yet designed — needs a distinct "unverifiable-by-scanning" caveat slot per DECISION 020, not just pass/fail findings | CLOSED — implemented in verdict.py's `skill_verdict()` (M6): a structurally separate "Caveats" section in both text and `--json` output, distinct from "Findings". Same late-discovered-at-close gap as OI-009 | 1 |
| OI-011 | Deferred from Socratic challenge (`new-project` skill, Step 2), not blocking today: undefined behavior when OSV.dev/GitHub/Anthropic API is down or rate-limited mid-scan (silent skip vs. loud failure vs. partial verdict) | CLOSED — M11: every pillar wrapped, degraded scans say so explicitly in both text and `--json`, verified with real network failures and monkeypatched exceptions | 1 |
| OI-012 | Deferred from Socratic challenge, not blocking today: scan-result reproducibility/versioning — no decision on whether a result records which ruleset version / data timestamp it used | CLOSED — M11: every verdict records scan_timestamp + ruleset_versions (code_scan, skill_scan, freshness_scan) | 1 |
| OI-013 | Deferred from Socratic challenge, not blocking today: false-positive/allowlist mechanism for legitimate patterns that resemble red flags — now has a concrete real example (browser-use SKILL.md's `printf ... \| auth login --api-key-stdin`, a secure secret-handling pattern that a naive "env var + pipe" rule would misflag; see KNOWLEDGE.md) | CLOSED — M11: `.repocheck-allow.json` suppression mechanism (suppression.py), category+path matching, reasons shown not hidden, type-validated after a crash was found and fixed | 1 |
| OI-014 | Deferred from Socratic challenge, not blocking today: whether full v1 scope (4 pillars × repo+skill modes × pluggable interfaces × 2 verdict templates) is realistic as one v1 for a solo builder, or is v1+v2 disguised as one milestone list | CLOSED — empirically answered: all 12 milestones shipped, verified, and released public in this session (agent-assisted, not literally one person's unaided effort — worth naming that distinction rather than overclaiming). The full scope was realistic, though it took substantially longer and more iteration (two rounds of independent adversarial QA, several real bugs) than the original v1/v2 framing anticipated | 1 |
| OI-015 | GitHub's hosted code-search API gave unreliable results for a quick pattern sweep during the validation trace — code red-flag pillar should fetch raw file content via the file-access interface (DECISION 012) and pattern-match locally, not depend on a host's search API | CLOSED — implemented from M4 onward: code_scan.py always fetches raw content via fetch_file/fetch_all_files and pattern-matches locally, never calls GitHub's search API. Same late-discovered-at-close gap as OI-009/OI-010 | 1 |
| OI-016 | M3's skill-instruction scan has only been tested against synthetic malicious examples (built from the research's description), not an actual sourced real-world malicious skill sample (e.g. Snyk's ToxicSkills dataset, Datadog Security Labs writeup). M3's acceptance criteria call for a real example — find and test one before M3 is truly DONE | CLOSED — sourced 2 real examples directly from Snyk's ToxicSkills research (Feb 2026 audit); both initially evaded detection, both fixed (credential-shaped env-var references, invisible-Unicode-character stripping), re-verified with zero regressions. See KNOWLEDGE.md | 2 |
| OI-017 | code_scan.py streams file content (solves memory scaling) but still costs one GitHub contents-API call per matched file (does not solve API-call-count scaling for repos with thousands of matching files). Capped at 300 files with an explicit note for now. Relevant to M9's deep scan too, which fetches some of the same files | CLOSED — FileAccessProvider.fetch_all_files() added, GitHub implementation uses one tarball download instead of N per-file calls, falls back gracefully if the tarball fetch fails (tested with a real monkeypatched failure). browser-use/browser-use: ~38s (concurrent-only) -> ~19s (bulk+concurrent), identical findings | 2 |
| OI-018 | freshness_scan.py supports PyPI and npm only. Go ecosystem freshness lookup is not implemented — the module proxy's version-listing API needs case-encoding handling for module paths with uppercase letters, not yet done | CLOSED — go_freshness() implemented with case encoding, verified against a real uppercase-path module (github.com/PuerkitoBio/goquery) and end-to-end against google/osv.dev's 3-ecosystem, 632-dependency real data | 2 |
| OI-019 | verdict.py's full pipeline takes ~6 minutes on a real 390-file repo — all sequential, uncached network calls across CVE/severity/code-scan/freshness pillars, no concurrency. Distinct from OI-017 (API-call count) — this is wall-clock time. Needs concurrency (e.g. asyncio or a thread pool) and/or caching before this is a pleasant CLI experience | CLOSED — concurrency.py (10-worker thread pool) applied to all 3 dominant loops, measured ~9x speedup (352s -> 38s) on the same repo, verified correctness unchanged, regression suite clean. Caching not implemented — separate, smaller remaining win, not blocking | 2 |
| OI-020 | M9 (deep_scan.py) is built (gating, error handling, high-risk selection, prompt-injection-safe delimiting) but NOT verified against a live Anthropic API call — no ANTHROPIC_API_KEY was available this session. `verify_deep_scan.py` is written and ready to run the moment a key exists; run it and update MILESTONES.md M9 to DONE once it passes | OPEN | 2 |
| OI-021 | code_scan.py's obfuscation co-occurrence check (long encoded blob + decode/exec call) is whole-file, not proximity-based — an unrelated safe eval() and an unrelated long constant elsewhere in the same file falsely co-occur. Real fix needs AST-level analysis, out of scope for the current regex-based static pass. Found by round-2 independent QA, documented as an accepted limitation for now, same tradeoff already accepted for credential-harvesting | OPEN | 2 |
