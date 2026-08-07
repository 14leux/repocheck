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

## Next up (Session 2) — BUILD ONLY, no further scoping

Stop-scoping trigger is active (recorded in MILESTONES.md M1). OI-007
through OI-015 do not block M2 — resolve them as the code needing them
gets written.

- [ ] M2: walking skeleton — Python, hardcoded GitHub + OSV.dev, repo URL → manifests → advisory list
- [ ] M2 acceptance: reproduce the M1 manual trace on `browser-use/browser-use` in code (pillow flagged, five deps clean)
- [ ] M2 acceptance: second different-ecosystem repo works with no code changes
- [ ] M2 acceptance: monorepo with manifests in different subdirectories finds both
- [ ] Add a real `.gitignore` before the first code commit
