# Contributing to RepoCheck

## Proposing a new red-flag pattern

RepoCheck's detection rules (in `code_scan.py` and `skill_scan.py`) are
a **versioned, human-reviewed ruleset that improves through normal
software releases** — the same model as ESLint or Semgrep rules. This
is a deliberate design choice (`DECISIONS.md` #001, #006): RepoCheck
never builds a live, self-updating threat feed, because an unattended
system that mutates its own detection logic can fail silently and
produce a false "safe" verdict with nobody noticing until it's too
late.

So a new pattern only ever ships as a normal, reviewed code change:

1. **Open an issue or PR describing the pattern**, ideally with a real
   example — either a real repo/skill that exhibited it, or, if it's
   from private/sensitive material, a synthetic example that reproduces
   the same structure.
2. **State what it catches and what it might false-positive on.** Every
   existing pattern in this codebase has a documented false-positive
   history — see `KNOWLEDGE.md` for several found by adversarial
   testing (an IP-blocking test fixture, a defensive description of an
   attack pattern, an embedded certificate). A new pattern proposed
   without thinking about its own false-positive shape will very likely
   have one; naming the risk up front is expected, not a red flag
   against the proposal.
3. **Add a test case**, both a true positive (the pattern should catch)
   and, where plausible, a true negative (something that looks similar
   but shouldn't be flagged). There's no formal test suite yet (see
   `MILESTONES.md`/Open Items) — for now, a short reproducible script
   showing the pattern firing correctly is enough, following the style
   already used throughout the codebase's own development (see
   `KNOWLEDGE.md`'s entries for the shape this usually takes).
4. **Bump the relevant `RULESET_VERSION` constant** (`code_scan.py`,
   `skill_scan.py`, or `freshness_scan.py`) so scans record which
   ruleset version produced their result — this is how RepoCheck stays
   reproducible over time (`DECISIONS.md` #012).

If a deep-scan (LLM reasoning) pass catches something the static
ruleset misses, that's the intended signal to propose a new static
pattern for it, not a reason to leave it only in the LLM's reach —
see `DECISIONS.md` #007.

## Other contributions

- **Bug reports**: if RepoCheck gives a wrong verdict (false positive
  *or* false negative), please include the repo/skill and the specific
  finding. Real examples are far more useful than descriptions —
  several of RepoCheck's own bugs were found this way (see
  `KNOWLEDGE.md`).
- **New ecosystems/hosts**: the file-access and dependency-ecosystem
  layers are designed as pluggable interfaces (`interfaces.py`,
  `DECISIONS.md` #012) with only GitHub and OSV.dev's covered
  ecosystems implemented in v1. A PR adding GitLab, Bitbucket, or a
  new ecosystem lookup is welcome, provided it implements the existing
  `FileAccessProvider` interface rather than adding a parallel path.
- **Known open items**: see the Open Items table in
  `.agent/instructions.md` for tracked gaps (e.g. Go-ecosystem
  freshness lookup, large-repo performance) that are open and welcome
  a PR.

## Non-negotiables

These apply to every contribution, no exceptions (see `CLAUDE.md`):

- Never execute anything belonging to a scanned repo or skill.
- Never build a local, self-mutating vulnerability database — CVE
  lookups are always live.
- Skill-mode scanning must cover `SKILL.md`/skill-manifest content by
  default, not only as an opt-in.
- Anything fed to the deep-scan LLM pass must be structurally delimited
  as untrusted data, never interpretable as instructions.

## Development notes

- Pure Python standard library, no external dependencies — please keep
  it that way unless there's a strong reason (raise it in an issue
  first).
- No formal package layout yet — each pillar is a standalone script
  that imports from `skeleton.py`'s shared parsing/fetching functions.
  This is intentional for now (`DECISIONS.md` #021: interfaces get
  extracted from working code, not designed speculatively) but will
  likely be revisited as the project grows.
