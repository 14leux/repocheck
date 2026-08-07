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
| 2 | Walking skeleton — repo → manifest → OSV.dev → CVE list, hardcoded | V1 | NOT STARTED |
| 3 | Skill-mode instruction scan | V1 | NOT STARTED |
| 4 | Repo-mode code red-flag scan | V1 | NOT STARTED |
| 5 | Dependency freshness signal | V1 | NOT STARTED |
| 6 | Severity model + humanized verdict (both modes) | V1 | NOT STARTED |
| 7 | Extract the pluggable interfaces from working code | V1 | NOT STARTED |
| 8 | CLI wrapper — first genuinely usable release | V1 | NOT STARTED |
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

**Acceptance criteria:**
- Run against `browser-use/browser-use` reproduces the M1 manual result:
  `pillow==12.2.0` flagged with its advisories, the five clean
  dependencies reported clean.
- Run against a second, different-ecosystem repo (npm or Go) returns
  sensible results without code changes.
- Walks the whole tree for manifests — a monorepo with `pyproject.toml`
  and `package.json` in different subdirectories finds both.
- Never clones, never installs, never executes anything from the target.

---

## M3 — Skill-mode instruction scan · V1

**Deliverable:** static pattern analysis of `SKILL.md` / skill manifest
content — the differentiated pillar (DECISION 015). Free, default, no
LLM call.

**Acceptance criteria:**
- Detects credential-access-plus-exfiltration phrasings, instruction-
  override phrasings, and shell-pipe-execute patterns in prose.
- Reports "fetches and follows external content at runtime" as its own
  caveat category, not a red flag (DECISION 020).
- Run against `browser-use/browser-use`'s real skills: reports the
  external-fetch caveat, and does **not** flag the
  `printf … | auth login --api-key-stdin` line as credential leakage
  (OI-013's recorded false-positive case).
- Written against at least one real known-malicious example, not only
  synthetic test strings.

---

## M4 — Repo-mode code red-flag scan · V1

**Deliverable:** static checklist over fetched source: obfuscation,
suspicious network calls, credential-harvesting patterns, install-time
scripts.

**Acceptance criteria:**
- Fetches raw file content and pattern-matches locally — does not depend
  on GitHub's hosted code-search API (OI-015).
- Scales to a large repo without loading everything into memory at once.
- Correctly finds no install hooks in `browser-use`'s `pyproject.toml`
  (M1's recorded true negative).

---

## M5 — Dependency freshness signal · V1

**Deliverable:** how far behind each declared dependency is.

**Acceptance criteria:**
- Produces a per-dependency lag figure and a repo-level summary.
- Distinguishes "pinned but current" from "pinned and abandoned" —
  `browser-use` pins everything exactly, which must not read as stale.

---

## M6 — Severity model + humanized verdict · V1

**Deliverable:** the piece that makes RepoCheck useful rather than
merely correct — combines M2–M5 into one traffic-light signal plus
plain-language narrative, in two templates (repo mode, skill mode).

**Acceptance criteria:**
- Severity model documented and defensible: how CVSS, red-flag risk,
  and freshness lag combine into one colour (OI-008).
- A single severe finding cannot be averaged away by many clean signals.
- Skill-mode template has a distinct slot for unverifiable-by-scanning
  caveats, separate from findings (OI-010, DECISION 020).
- Every finding explains what it is, why it's risky, and what a real
  attack using it looks like — readable by someone who does not know
  what a CVE is (DECISION 009).
- Pre-flight state reports scope and rough time before scanning starts.
- `--json` emits the same findings structurally.
- Verdict on `browser-use` is one a security-literate reader would
  agree with — no false alarm, no false reassurance.

---

## M7 — Extract the pluggable interfaces · V1

**Deliverable:** refactor M2–M6's working code behind the two interfaces
Decisions 012 and 018 require — file-access (GitHub the only
implementation) and model-provider (Anthropic the only implementation).

**Acceptance criteria:**
- All M2–M6 acceptance criteria still pass after the refactor.
- Adding a second implementation of either interface requires no change
  to calling code — demonstrated by a stub, not asserted.

---

## M8 — CLI wrapper · V1

**Deliverable:** `repocheck <url>` — the first genuinely usable release.
V1 is done when this works.

**Acceptance criteria:**
- Runs the full static pipeline and prints the M6 verdict.
- Auto-detects repo vs. skill mode, with an explicit override flag.
- Contains no scan logic — a wrapper only (DECISION 002).
- Mailu can vet a real repo with it faster than doing it by hand.

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
