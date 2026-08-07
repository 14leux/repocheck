## Session 1 — Scoping (done this session)

- [x] Decide: Claude Code skill only, vs. standalone repo/CLI/service — chose both, sharing one core library (DECISIONS.md #002)
- [x] Decide concretely what "safe" checks for — chose full README scope: CVEs + code red flags + dependency freshness + plain-language verdict (DECISIONS.md #003)
- [x] Decide how much of `PROJECT_DISCIPLINE.md`'s apparatus this project needs — lightweight subset (DECISIONS.md #004)
- [x] Decide the public-repo plan — MIT license, public from day one (DECISIONS.md #005)
- [x] Confirm the "live lookup, not self-mutating local DB" design decision still holds — reconfirmed (DECISIONS.md #001)

## Session 1 continued — further scoping (done this session)

- [x] Web interface — confirmed out of scope for v1 (revisit once CLI+skill are proven)
- [x] Novel/emerging attack pattern coverage — hybrid static ruleset + opt-in deep scan (DECISIONS.md #007)
- [x] "Learning" over time reconciled with Decision 001 — versioned, human-reviewed ruleset releases, not a live self-mutating feed (DECISIONS.md #006)
- [x] Full GitHub *projects* (not just skills) confirmed in scope — surfaces monorepo/multi-ecosystem manifest walking as a real requirement, not hypothetical
- [x] Cost model — static scan free/default, deep scan opt-in, costs tokens (skill) or API usage (CLI) (DECISIONS.md #008)
- [x] Output UX — humanized language for both findings and upfront cost/time expectations (DECISIONS.md #009)
- [x] Time estimation approach — pre-flight estimate for static scan (file/dep count), post-static-pass estimate for deep scan (flagged-file count, not repo size)

## Session 1 continued further — five open items resolved (done this session)

- [x] Core library language/runtime — Python (DECISIONS.md #010)
- [x] Primary CVE/advisory data source — OSV.dev (DECISIONS.md #011)
- [x] v1 git-host/ecosystem scope — GitHub-only host behind pluggable interface, ecosystem breadth via OSV.dev (DECISIONS.md #012)
- [x] Verdict/report format — traffic-light + narrative primary, JSON via flag (DECISIONS.md #013)
- [x] CLI deep-scan API key mechanism — ANTHROPIC_API_KEY env var only (DECISIONS.md #014)

## Session 1 continued further still — council review (done this session)

- [x] Ran llm-council pressure-test on full v1 plan — transcript at `council-transcript-20260807T000000.md`
- [x] Council found and validated a real gap: code-only red-flag checklist misses skill-instruction-injection attacks (dominant threat for skills per 2026 research) — fixed via DECISIONS.md #015
- [x] Distinct repo/skill scan modes locked in, skill mode gets a default free instruction-content analysis pass (DECISIONS.md #015)
- [x] Deep-scan prompt-injection-safe handling made a non-negotiable, added to CLAUDE.md (DECISIONS.md #016)
- [x] Confirmed CLI is agent-agnostic by construction (works with Codex, Antigravity, any shell-capable agent); other native agent wrappers follow the same thin-wrapper pattern, none in v1 scope (DECISIONS.md #017)

## Session 1 continued once more — provider-agnostic deep scan (done this session)

- [x] Amended DECISIONS.md #014 — deep-scan model provider is now a pluggable interface, Anthropic-only in v1, matching the agnostic pattern used for git host/ecosystem/coding agent (DECISIONS.md #018)

## Session 1 continued once more — new-project skill audit + validation trace (done this session)

- [x] Ran `new-project` skill in Spec Mode as a discipline audit — reaffirmed lightweight scaffold (DECISIONS.md #019), classified primary purpose as Leverage > Learning > Revenue (DECISIONS.md #019)
- [x] Socratic challenge run — 3 assumption/gap/constraint challenges raised, all deferred as PENDING (OI-011 through OI-014), not blocking
- [x] Ran `new-project`'s 5-advisor council — converged (again, independently of the earlier 8-advisor llm-council) on "validate before building more"
- [x] Actually ran the validation trace this time: manually traced `github.com/browser-use/browser-use` through the planned CVE lookup, install-hook check, and skill-instruction analysis
- [x] OSV.dev batch lookup confirmed working with real data (pillow==12.2.0 → 26 real advisories; 5 other deps clean) — first real proof the mechanism works
- [x] Found and recorded a real risk category the plan hadn't named: dynamic external-content fetch-and-follow in skill instructions (DECISIONS.md #020) — common in legitimate skills, structurally identical to the primary attack vector, must be an honest caveat not a red flag
- [x] Found and recorded a real false-positive example for the deferred allowlist question (OI-013) — secure stdin secret-piping that a naive pattern rule would misflag
- [x] Noted GitHub's hosted code-search API is unreliable for pattern sweeps — code checklist should scan raw fetched content locally (OI-015)

## Session 1 — milestones rewritten (done this session)

- [x] Rewrote MILESTONES.md — 12 milestones grouped V1 / Hardening / Release, each with falsifiable acceptance criteria tied to the real `browser-use` trace results
- [x] Recorded the build resequencing as DECISIONS.md #021 — prove mechanisms first, extract interfaces in M7 (supersedes sequencing guidance in #012/#018, not their substance)
- [x] Defined what "V1 done" means: M1–M8, ending at a working CLI Mailu can actually vet repos with

## Session 2 — M2 walking skeleton (done this session)

- [x] Added real `.gitignore` before first code commit
- [x] M2: `skeleton.py` — Python stdlib-only, hardcoded GitHub + OSV.dev, repo URL → manifests → advisory list
- [x] M2 acceptance: reproduced the M1 manual trace on `browser-use/browser-use` in code — pillow flagged with same 26 advisories, plus found 2 more real vulns (click, mcp)
- [x] M2 acceptance: second different-ecosystem repo (expressjs/express, npm) works with zero code changes
- [x] M2 acceptance: monorepo with manifests in different subdirectories (google/osv.dev — 19 manifests, 3 ecosystems) finds all of them
- [x] Confirmed by construction: never clones, never installs, never executes anything from scanned repo

## Session 2 — M3 skill-mode instruction scan (done this session, one gap flagged)

- [x] M3: `skill_scan.py` — static pattern analysis of SKILL.md content (DECISIONS.md #015), three categories: credential-exfil, instruction-override, shell-pipe-execute, plus the fetch-and-follow caveat (DECISIONS.md #020)
- [x] M3 acceptance: tested against browser-use's real skill — external-fetch caveat correctly reported, `api-key-stdin` pattern correctly NOT flagged (OI-013's recorded case, resolved)
- [x] M3 acceptance: three synthetic true-positive tests (credential-exfil, instruction-override, curl|bash) — all caught
- [ ] M3 acceptance NOT met: needs a test against a real sourced malicious sample, not just synthetic examples — OI-016

## Session 2 — M4 repo-mode code red-flag scan (done this session)

- [x] M4: `code_scan.py` — obfuscation, credential-harvesting, suspicious network calls, install-time scripts; streams file-by-file, doesn't depend on GitHub search API (OI-015 resolved for this pillar)
- [x] M4 acceptance: no install hooks found in browser-use's pyproject.toml (M1's recorded true negative), verified directly
- [x] M4 acceptance: memory-scaling met by construction (fetch/scan/discard one file at a time)
- [x] Bonus validation: true negative on a real repo (itsdangerous), true positives on all 4 categories via synthetic examples
- [x] Flagged OI-017: API-call-count scaling (distinct from memory scaling) not yet solved, capped at 300 files for now

## Session 2 — M5 dependency freshness signal (done this session)

- [x] M5: `freshness_scan.py` — PyPI + npm freshness lookup, per-dependency lag + repo-level summary
- [x] M5 acceptance: browser-use's exact-pinning style correctly not conflated with staleness (33/36 current or actively-maintained)
- [x] Real bug caught and fixed via testing: `classify()` mislabeled a genuinely abandoned package as "current" because no newer version existed — fixed to check abandonment independent of "pinned == latest"
- [x] True-positive confirmed post-fix (`nose==1.3.7`, 11 years stale) and true-negative reconfirmed on browser-use after the fix
- [x] Flagged OI-018: Go ecosystem freshness lookup not implemented

## Session 2 -- M6 severity model + humanized verdict (done this session)

- [x] M6: `verdict.py` -- combines CVE/code-scan/freshness (repo mode) or instruction-scan (skill mode) into traffic-light + narrative, two templates, `--json` flag
- [x] Real bug fixed: private/loopback/reserved IPs were flooding findings with false positives from browser-use's own test fixtures (107 -> 58 findings, zero real signal lost)
- [x] Real bug fixed: pre-flight text was corrupting `--json` stdout output -- routed to stderr
- [x] Pre-flight estimate now computed from actual scope, not a static claim
- [x] Final verdict on browser-use: CAUTION, driven by real HIGH-severity CVEs -- a security-literate reader would agree with this
- [x] Flagged OI-019: ~6 minute wall-clock time on a large repo, no concurrency yet

## Session 2 -- M7 extract the pluggable interfaces (done this session)

- [x] M7: `interfaces.py` (FileAccessProvider, ModelProvider) + `github_provider.py` (the GitHub implementation, moved verbatim)
- [x] `skeleton.py` refactored to delegate through a swappable module-level provider -- zero changes needed to skill_scan.py, code_scan.py, freshness_scan.py, verdict.py
- [x] M7 acceptance: all M2-M6 results re-verified identical after the refactor
- [x] M7 acceptance: `test_provider_swap.py` proves swappability with a real fake provider, not just asserted
- [x] ModelProvider forward-defined for M9 (honest limitation: no working code exists yet to extract it from)

## Session 2 -- M8 CLI wrapper, V1 COMPLETE (done this session)

- [x] M8: `repocheck.py` -- CLI wrapper, zero scan logic, auto-detects mode from 3 real usage patterns (bare repo, path arg, pasted GitHub blob URL)
- [x] M8 acceptance: `--json` verified end to end through the CLI, both modes
- [x] **V1 COMPLETE: M1-M8 all DONE**

## Next up (Session 3) -- Hardening phase (M9-M12), not V1-blocking

- [ ] M9: opt-in deep scan (LLM reasoning pass) -- needs prompt-injection-resistant handling verified with a deliberate injection attempt (DECISIONS.md #016)
- [ ] M10: Claude Code skill wrapper -- resolve OI-007 (call mechanism) here, not before
- [ ] M11: degraded-state handling (OI-011), reproducibility/versioning (OI-012), false-positive/allowlist mechanism (OI-013)
- [ ] M12: public release polish, flip repo from private to public (DECISIONS.md #022)
- [ ] OI-016: find and test against a real malicious skill sample to fully close M3
- [ ] OI-017: API-call-count scaling for large repos
- [ ] OI-018: Go ecosystem freshness lookup
- [ ] OI-019: concurrency/caching for verdict.py's ~6min wall-clock time on large repos
