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

## Session 2 -- M9 opt-in deep scan, built but not fully verified (done this session)

- [x] M9: `anthropic_provider.py` (AnthropicModelProvider, raw HTTP, no SDK dependency) + `deep_scan.py` (high-risk selection, prompt-injection-safe prompt, opt-in `--confirm` gate)
- [x] M9 acceptance: opt-in gating verified (no --confirm = zero API calls)
- [x] M9 acceptance: missing-API-key error verified (specific, actionable message)
- [x] M9 acceptance: high-risk file selection verified against 2 real repos
- [ ] M9 acceptance NOT verified: prompt-injection resistance needs a live API call (OI-020)
- [ ] M9 acceptance NOT verified: "catches what static misses" needs a live API call -- test case itself confirmed valid (paraphrase evades regex), `verify_deep_scan.py` ready to run

## Session 2 -- M10 Claude Code skill wrapper (done this session)

- [x] M10: `skills/repocheck/SKILL.md` -- the skill wrapper itself, instructs shell-out to repocheck.py for static scan, in-session reasoning for deep review (resolves OI-007, DECISION 023)
- [x] M10 acceptance: dogfooding found and fixed a real false positive -- RepoCheck's own defensive description of the instruction-override pattern tripped its own detector
- [x] Fixed with a descriptive-context guard in skill_scan.py, re-verified against M3's true-positive test and the browser-use acceptance case (no regression)

## Session 2 -- M11 done, two rounds of independent QA, real bugs found and fixed (done this session)

- [x] Dispatched 2 independent adversarial-QA subagents (not self-testing) against M9-M11's work, per Mailu's explicit request
- [x] Round 1 found 7 real bugs: npm caret-ranges treated as exact pins, 2 crash paths (no top-level error handling), M10's guard overfit, 4 detection evasions, an obfuscation false positive, a suppression type-crash, missing freshness ruleset version
- [x] Fixed all 7, verified each with real command output (not just re-reading the code)
- [x] Round 2 re-verified round 1's fixes independently and found each still had an edge: parse_repo_arg's own fix had new bugs, exit code was 0 on failure, M10's guard still had 2/5 new false positives, more HTTP-library evasions (httpx/aiohttp/axios/Go/PowerShell), a second obfuscation false-positive shape
- [x] Fixed what's reasonably fixable (parse_repo_arg rewritten stricter, exit code now reflects scan health, guard broadened further, 5 more patterns added, .ps1 now scanned)
- [x] Documented OI-021 (proximity vs. whole-file co-occurrence) as an accepted limitation rather than chased further -- real fix needs AST analysis
- [x] Cleaned up stray debug files left by subagent testing (err*.log, out*.json)
- [x] M11 acceptance criteria (OI-011/012/013) all met and verified
- [x] OI-008 (severity model) retroactively closed -- was implemented in M6 but never marked closed

## Session 2 -- M12 public release polish, ALL 12 MILESTONES COMPLETE (done this session)

- [x] M12: README.md rewritten for real usage (install, usage, glossary, all four DECISIONS.md/KNOWLEDGE.md/MILESTONES.md pointers)
- [x] M12 acceptance: install instructions verified -- zero external deps confirmed by grep, GITHUB_TOKEN-optional claim re-tested with it unset
- [x] M12: CONTRIBUTING.md written -- red-flag-rule proposal process per DECISIONS.md #006
- [x] M12: glossary folded into README.md per DECISIONS.md #019
- [x] M12: repo flipped private -> public, confirmed via gh api
- [x] M12: default branch renamed master -> main, old branch deleted from remote
- [x] Final safety scan for accidentally committed secrets before/after going public -- clean

## Session 2 continued -- OI-019 concurrency fix (done this session)

- [x] `concurrency.py` -- 10-worker thread pool, applied to code-scan file fetches, CVE severity lookups, freshness lookups, npm registry lookups
- [x] Measured real improvement on browser-use/browser-use: ~352s -> ~38s (~9x)
- [x] Verified correctness unchanged (same finding shape) and full regression suite still passes
- [x] Pre-flight time estimate recalibrated against the real measurement, not re-guessed

## Session 2 continued -- OI-016 closed with real research (done this session)

- [x] Sourced 2 real examples from Snyk's actual ToxicSkills research (not another synthetic test)
- [x] Real example 1 (credential-shaped env var exfil via URL params) confirmed MISSED, fixed by extending SENSITIVE_PATH_PATTERNS + EXFIL_VERB_PATTERNS
- [x] Real example 2 (invisible Unicode character concealment) confirmed a genuine evasion, fixed with strip_invisible_characters() at the normalization layer (skeleton.py, shared by both scanners)
- [x] Both fixes verified with zero regressions (browser-use, dogfooding, itsdangerous all identical)
- [x] M3 now fully DONE, all 4 acceptance criteria met

## Session 2 continued -- OI-018 Go freshness lookup (done this session)

- [x] go_freshness() implemented with Go module proxy case encoding
- [x] Verified against a real uppercase-path module (github.com/PuerkitoBio/goquery) -- confirms the encoding actually works, not just passes on already-lowercase paths
- [x] Ran end-to-end against google/osv.dev (632 deps, 3 ecosystems) -- Go now reports real freshness data
- [x] Found and fixed a gap: freshness_scan.py's own standalone scan() had never gotten the OI-019 concurrency fix (only verdict.py's inline pillar had it)

## Session 2 continued -- OI-017 API-call-count fix (done this session)

- [x] FileAccessProvider.fetch_all_files() added -- default per-file fallback, GitHub override uses one tarball download
- [x] Verified correctness (identical 60 findings) and speed (~38s -> ~19s) against browser-use/browser-use
- [x] Verified the fallback path for real -- monkeypatched a tarball failure, confirmed graceful degradation to per-file fetch, not a crash
- [x] M7's provider-swap demonstration (test_provider_swap.py) still passes untouched -- confirms the new interface method's default-per-file design didn't break backward compatibility
- [x] Pre-flight time estimate recalibrated for the new architecture

## Session close reconcile -- found 4 stale Open Items (done this session)

- [x] OI-009, OI-010, OI-015 were genuinely resolved during M3/M4/M6 but never marked CLOSED in the table -- fixed
- [x] OI-014 (v1 scope realistic for a solo builder?) closed with the empirical answer -- yes, all 12 milestones shipped
- [x] tasks/codebase_map.md reconciled -- fixed a broken table (stray blank line), 3 stale descriptions, consolidated 3 function-level rows into their parent file entries

## Session 3 -- rebrand + humanized README + API key hygiene

- [x] Renamed display name to "Dr. RepoCheck" (README, SKILL.md heading,
      repocheck.py docstring banner) -- technical identifiers (repo URL,
      module names, `name: repocheck` slug, CLI invocation) left
      unchanged deliberately, see DECISIONS.md #024
- [x] Rewrote README intro in humanized, psychology-informed language
      (social proof, optimism bias, vibe-coding trust-speed framing) for
      a reader new to security review, not a security specialist
- [x] Added "Protecting your API key" README section (env vars, expiring
      keys via Anthropic Console 3h/1d/7d/30d/custom/never, workspace
      scoping, rotation cadence, do/don't list) plus a "why RepoCheck
      asks for your own key" explainer -- sourced from Anthropic's docs
      and the OWASP Secrets Management Cheat Sheet, not assumed
- [x] Surfaced a short key-hygiene pointer at the two places a user
      actually meets the ask: anthropic_provider.py's MissingApiKeyError
      message, deep_scan.py's preflight() output

## Next up (Session 4+) -- tracked technical debt, no milestones left

All 12 milestones are DONE. Remaining work is tracked open items, not
blocking anything:

- [ ] OI-020: run `verify_deep_scan.py` once ANTHROPIC_API_KEY is available, flip M9 fully DONE
- [ ] OI-021: proximity-based obfuscation co-occurrence (needs AST analysis)
