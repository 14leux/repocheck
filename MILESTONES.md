# MILESTONES.md

Status legend: `NOT STARTED` / `IN PROGRESS` / `DONE`

**What "V1 done" means:** Mailu can point RepoCheck at a GitHub repo or
a Claude Code skill and get a trustworthy, humanized verdict — the
PixelRAG-style manual review that started this project, automated. V1 is
M1–M8. Everything from M9 on is hardening and public release, not
required for the tool to be genuinely useful to its first user
(Leverage-first, per DECISION 019).

**Sequencing principle (from the session-1 councils):** prove each
detection mechanism against a real target *before* building abstraction
around it. Interfaces get extracted from working code (M7), not designed
up front — see DECISION 021.

| # | Milestone | Phase | Status |
|---|-----------|-------|--------|
| 1 | Scoping and validation | Scope | DONE |
| 2 | Walking skeleton — repo → manifest → OSV.dev → CVE list, hardcoded | V1 | DONE |
| 3 | Skill-mode instruction scan | V1 | IN PROGRESS — 3 of 4 acceptance criteria met, real-malicious-sample test outstanding (OI-016) |
| 4 | Repo-mode code red-flag scan | V1 | DONE |
| 5 | Dependency freshness signal | V1 | DONE |
| 6 | Severity model + humanized verdict (both modes) | V1 | DONE |
| 7 | Extract the pluggable interfaces from working code | V1 | DONE |
| 8 | CLI wrapper — first genuinely usable release | V1 | DONE — **V1 COMPLETE** |
| 9 | Opt-in deep scan (LLM reasoning pass) | Hardening | NOT STARTED |
| 10 | Claude Code skill wrapper | Hardening | NOT STARTED |
| 11 | Degraded-state, reproducibility, false-positive handling | Hardening | NOT STARTED |
| 12 | Public release polish | Release | NOT STARTED |

---

## M1 — Scoping and validation · DONE

**Deliverable:** project shape, v1 scope, discipline level, license, and
all major technical decisions recorded; core detection mechanism
validated against a real repo before any code written.

**Acceptance criteria — all met:**
- 21 DECISIONS.md entries covering shape, cost model, detection
  architecture, output format, host/ecosystem/provider scope.
- Two independent councils run (8-advisor llm-council, 5-advisor
  new-project), both surfacing findings that changed the plan.
- Manual validation trace executed against a real 108k-star repo,
  results recorded in KNOWLEDGE.md.
- Lightweight discipline file set exists and is current.

**Lessons learned:**
- Both councils independently converged on "validate before building
  more" — and the first council's recommendation went unexecuted until
  the second one repeated it. A recommendation that isn't scheduled
  isn't a recommendation.
- The validation trace found in ~20 minutes what neither council caught
  in full: the TOCTOU gap in skills that fetch external content at
  runtime (DECISION 020), and a concrete false-positive example
  (OI-013). Reasoning about a mechanism is not a substitute for running
  it once.
- Scoping produced 21 decisions and zero lines of code. That is the
  correct ratio for day one and would be the wrong ratio for day two —
  M2 starts with code (see the stop-scoping trigger below).

**Stop-scoping trigger (from council peer review):** Session 2 is
build-only. Open items OI-007 through OI-015 do not block M2 and are
resolved as the code that needs them gets written, not in advance.

---

## M2 — Walking skeleton · V1

**Deliverable:** one hardcoded end-to-end path in Python: GitHub repo
URL in → manifest files found and parsed → OSV.dev batch query → list of
real advisories printed. No interfaces, no abstraction, no polish. This
is the manual validation trace from M1, in code.

**Acceptance criteria — all met (session 2):**
- Run against `browser-use/browser-use` reproduces the M1 manual result:
  `pillow==12.2.0` flagged with its advisories, the five clean
  dependencies reported clean. Exceeded: found 2 more real
  vulnerabilities (`click`, `mcp`) M1's 6-dependency manual sample
  never checked.
- Run against a second, different-ecosystem repo (npm) returned sensible
  results with zero code changes — `expressjs/express`,
  `body-parser==2.2.1` flagged.
- Walks the whole tree for manifests — `google/osv.dev` (19 manifests,
  3 ecosystems, across subdirectories) found all of them, 632
  dependencies checked, 9 real advisories found including in OSV.dev's
  own dependencies.
- Never clones, never installs, never executes anything from the
  target — confirmed by construction (GitHub contents API + OSV.dev
  query API only).

**Lessons learned:** see KNOWLEDGE.md "Session 2 — M2 walking
skeleton." Notably: automating the check found more than the manual
spot-check did (full coverage vs. sampling); ecosystem-agnostic design
paid off immediately (npm worked with zero code changes); Windows
console cp1252 encoding needs the same fix as the user's other
projects; GitHub's tree API truncation path is implemented but still
untested against a repo large enough to trigger it.

---

## M3 — Skill-mode instruction scan · V1

**Deliverable:** static pattern analysis of `SKILL.md` / skill manifest
content — the differentiated pillar (DECISION 015). Free, default, no
LLM call.

**Acceptance criteria — mostly met (session 2), one gap flagged honestly:**
- Detects credential-access-plus-exfiltration phrasings, instruction-
  override phrasings, and shell-pipe-execute patterns in prose. **Met** —
  verified against three synthetic examples built directly from the
  patterns named in the 2026 research and DECISIONS.md #015/#020: all
  three caught.
- Reports "fetches and follows external content at runtime" as its own
  caveat category, not a red flag (DECISION 020). **Met** — fired
  correctly against browser-use's real skill, named `github.com`.
- Run against `browser-use/browser-use`'s real skills: reports the
  external-fetch caveat, and does **not** flag the
  `printf … | auth login --api-key-stdin` line as credential leakage
  (OI-013's recorded false-positive case). **Met** — zero false
  positives.
- Written against at least one real known-malicious example, not only
  synthetic test strings. **NOT met.** The three test cases are
  synthetic — built from the research's *description* of attack
  patterns, not an actual sourced malicious sample (e.g. from Snyk's
  ToxicSkills dataset or the Datadog Security Labs writeup cited in
  session 1). Recorded honestly rather than claimed done. Follow-up:
  OI-016.

**Lessons learned:** see KNOWLEDGE.md "Session 2 — M3 skill-mode
instruction scan." Notably: this is the first detection category proven
against both true positives and true negatives, not just "stays quiet on
safe content" — closes the Contrarian's session-1 concern. The
allowlist-vs-red-flag distinction needed a full-line check around each
match, not a bare pattern match, designed that way from the OI-013
example rather than discovered as a bug.

---

## M4 — Repo-mode code red-flag scan · V1

**Deliverable:** static checklist over fetched source: obfuscation,
suspicious network calls, credential-harvesting patterns, install-time
scripts.

**Acceptance criteria — all met (session 2):**
- Fetches raw file content and pattern-matches locally — does not depend
  on GitHub's hosted code-search API (OI-015). Met by construction.
- Scales to a large repo without loading everything into memory at once.
  Met — fetches, scans, discards one file at a time. (API-call *count*
  still scales with matched-file count, a separate concern — OI-017.)
- Correctly finds no install hooks in `browser-use`'s `pyproject.toml`
  (M1's recorded true negative). Verified directly.
- Also verified true negative on a real repo (`pallets/itsdangerous`,
  17 files, zero findings) and true positives on all four categories
  via synthetic examples (obfuscation, credential-harvesting, raw-IP
  network call, `package.json` install hook) — exceeds what the
  acceptance criteria explicitly required.

**Lessons learned:** see KNOWLEDGE.md "Session 2 — M4 repo-mode code
red-flag scan." Notably: streaming solves memory scaling but not
API-call-count scaling — two genuinely different problems, only one of
which this milestone's acceptance criteria asked for (OI-017, relevant
again at M9).

---

## M5 — Dependency freshness signal · V1

**Deliverable:** how far behind each declared dependency is.

**Acceptance criteria — all met (session 2):**
- Produces a per-dependency lag figure and a repo-level summary. Met —
  `freshness_scan.py` reports versions-behind and days-since-latest-
  release per dependency, plus a repo-level count by status.
- Distinguishes "pinned but current" from "pinned and abandoned" —
  `browser-use` pins everything exactly, which must not read as stale.
  Met, in the criterion's actual intent: exact-pinning style is not
  conflated with staleness (33 of 36 dependencies correctly show as
  current or actively-maintained-but-behind). 3 real dependencies
  (`InquirerPy`, `screeninfo`, `uuid7`) correctly show as genuinely
  abandoned upstream (4+ years since last release) — a true finding,
  not a false positive from the pinning style. See KNOWLEDGE.md for why
  this isn't a regression despite initially looking like one.

**Lessons learned:** see KNOWLEDGE.md "Session 2 — M5 dependency
freshness signal." A real classification bug was caught by testing
against a genuinely abandoned package (`nose==1.3.7`) — the first
version conflated "no newer version exists" with "current," which are
different things when the package's only release is over a decade old.

---

## M6 — Severity model + humanized verdict · V1

**Deliverable:** the piece that makes RepoCheck useful rather than
merely correct — combines M2–M5 into one traffic-light signal plus
plain-language narrative, in two templates (repo mode, skill mode).

**Acceptance criteria — all met (session 2), two real bugs found and fixed:**
- Severity model documented and defensible: how CVSS, red-flag risk,
  and freshness lag combine into one colour (OI-008). Met — weighted
  critical/high/moderate/low, documented in `verdict.py`'s docstring.
- A single severe finding cannot be averaged away by many clean signals.
  Met — `aggregate_color()` takes the maximum weight, never an average.
- Skill-mode template has a distinct slot for unverifiable-by-scanning
  caveats, separate from findings (OI-010, DECISION 020). Met — verified
  in both text and `--json` output.
- Every finding explains what it is, why it's risky, and what a real
  attack using it looks like — readable by someone who does not know
  what a CVE is (DECISION 009). Met — `EXPLANATIONS` dict, rendered per
  finding.
- Pre-flight state reports scope and rough time before scanning starts.
  Met, after a fix — originally a static "seconds to low minutes" claim
  that was simply wrong for a large repo; now computed from actual
  manifest/candidate-file counts, came within ~25% of real wall-clock
  time on the one test run.
- `--json` emits the same findings structurally. Met, after a bug fix —
  the pre-flight message was printing to stdout and corrupting the JSON
  output; fixed by routing all progress text to stderr.
- Verdict on `browser-use` is one a security-literate reader would
  agree with — no false alarm, no false reassurance. Met, after a bug
  fix — the code red-flag pillar was flooding the verdict with 75+
  false positives from `browser-use`'s own IP-blocking test fixtures;
  fixed at the detection-rule level (private/loopback/reserved IPs
  excluded outright, not a test-file suppression). Final verdict:
  CAUTION, driven by real HIGH-severity CVEs, findings dropped from 107
  to 58 purely by removing noise.

**Lessons learned:** see KNOWLEDGE.md "Session 2 -- M6 severity model +
humanized verdict." Both bugs here were caught only by running the full
pipeline against a real, large repo end to end — neither would have
surfaced from the smaller, more targeted tests used in M2-M5. The
6-minute wall-clock time on `browser-use` (390 candidate files, fully
sequential network calls, no concurrency) is real and recorded as
OI-019, distinct from OI-017's API-call-*count* concern.

---

## M7 — Extract the pluggable interfaces · V1

**Deliverable:** refactor M2–M6's working code behind the two interfaces
Decisions 012 and 018 require — file-access (GitHub the only
implementation) and model-provider (Anthropic the only implementation).

**Acceptance criteria — both met (session 2):**
- All M2–M6 acceptance criteria still pass after the refactor. Met —
  re-ran M2 (browser-use CVE list, identical), M3 (skill-scan caveat,
  identical), M4 (itsdangerous clean scan, identical), M5 (browser-use
  freshness, 3 abandoned, identical), and smoke-tested M6 (verdict.py
  both modes) after the refactor. Zero regressions.
- Adding a second implementation of either interface requires no change
  to calling code — demonstrated by a stub, not asserted. Met, for
  `FileAccessProvider` — `test_provider_swap.py`'s `FakeFileAccessProvider`
  proves `skeleton.py` and `code_scan.py` work unmodified against it.
  `ModelProvider` is forward-defined only (no M9 code exists yet to
  extract from or demonstrate a swap against) — an honest, recorded
  limitation, not a gap in this criterion's own scope.

**Lessons learned:** see KNOWLEDGE.md "Session 2 -- M7 extract the
pluggable interfaces." The chokepoint DECISION 021 bet on already
existed cheaply, because every script already imported
`list_tree`/`fetch_file` from one place rather than calling GitHub
directly -- confirms the sequencing bet (prove mechanisms first,
extract interfaces from working code) was right, not just defensible in
theory.

---

## M8 — CLI wrapper · V1

**Deliverable:** `repocheck <url>` — the first genuinely usable release.
V1 is done when this works.

**Acceptance criteria — all met (session 2):**
- Runs the full static pipeline and prints the M6 verdict. Met, both
  modes, `--json` verified end to end through the CLI.
- Auto-detects repo vs. skill mode, with an explicit override flag. Met
  -- three real UX paths tested: bare `owner/repo` (repo mode), a
  second positional path argument (skill mode), and pasting a full
  GitHub blob URL to a `SKILL.md` (auto-extracts owner/repo/path, skill
  mode) -- plus `--mode`/`--path` for explicit override.
- Contains no scan logic — a wrapper only (DECISION 002). Met by
  construction -- 90 lines, argument parsing and mode detection only,
  every actual scan call delegated to `verdict.py`.
- Mailu can vet a real repo with it faster than doing it by hand. Met
  -- `repocheck.py owner/repo` does in seconds-to-minutes what the
  project's origin story (manually reviewing PixelRAG) took a human
  session to do.

**V1 IS COMPLETE.** M1 through M8 all DONE. Every pillar validated
against real repos (not just synthetic tests), with two genuine bugs
(M5's abandoned-package misclassification, M6's IP false-positive
flood) caught by that validation and fixed before being called done.
One honest gap remains tracked, not hidden: M3's acceptance criteria
call for a test against a real sourced malicious sample, and only
synthetic examples exist so far (OI-016).

**Lessons learned:** see KNOWLEDGE.md "Session 2 -- M8 CLI wrapper (V1
complete)."

---

## M9 — Opt-in deep scan · Hardening

**Deliverable:** the targeted LLM reasoning pass over high-risk files
(DECISION 007), opt-in and never automatic.

**Acceptance criteria:**
- All scanned content structurally delimited as untrusted data — a
  malicious `SKILL.md` cannot influence the analysis (DECISION 016).
  Verified with a deliberate injection attempt, not assumed.
- Cost and rough time stated before it runs; refuses to run without an
  explicit opt-in.
- Clear specific error when `ANTHROPIC_API_KEY` is unset (DECISION 014).
- `SKILL.md`/skill manifests always treated as high-risk (DECISION 015).
- Catches at least one thing the static passes missed on a real example.

---

## M10 — Claude Code skill wrapper · Hardening

**Deliverable:** RepoCheck usable from inside a Claude Code session.

**Acceptance criteria:**
- Call mechanism decided and documented (OI-007).
- No scan logic in the wrapper.
- Deep scan runs on the session rather than requiring a separate key.
- RepoCheck scans its own `SKILL.md` clean — dogfooding.

---

## M11 — Degraded state, reproducibility, false positives · Hardening

**Deliverable:** the three deferred robustness gaps (OI-011, OI-012,
OI-013), which matter once other people rely on the output.

**Acceptance criteria:**
- A source being down or rate-limited never silently looks like a clean
  result — degraded scans say so in the verdict (OI-011).
- Every result records ruleset version and scan timestamp (OI-012).
- A documented suppression mechanism for known-good patterns, with the
  `api-key-stdin` case as its first test (OI-013).

---

## M12 — Public release polish · Release

**Deliverable:** the repo is something a stranger can use and contribute
to.

**Acceptance criteria:**
- README rewritten for real usage, not idea capture.
- Install instructions verified on a clean machine.
- Contribution guidelines, including how a new red-flag rule gets
  proposed and reviewed (DECISION 006).
- Glossary for non-expert readers (DECISION 019).
- LICENSE present (done) and `.gitignore` real.
- **Repository flipped from private to public** (DECISION 022), and the
  `master` → `main` default-branch rename settled either way.
