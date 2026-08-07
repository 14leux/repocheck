# tasks/context.md

**Status:** CLOSED

## Session 1 — Scoping and validation

**Goal:** Take RepoCheck from idea-capture (a README and a todo list, no
code, no discipline files) to a fully scoped project with a validated
detection mechanism and a real build plan.

**What was done:**

Set up the lightweight `PROJECT_DISCIPLINE.md` §10 file set — CLAUDE.md,
`.agent/instructions.md`, DECISIONS.md, MILESTONES.md, KNOWLEDGE.md,
codebase_map.md, context.md, wip.md — and LICENSE (MIT).

Resolved every scoping question the original README left open, plus a
lot it did not anticipate, across **21 DECISIONS.md entries**: ships as
both a Claude Code skill and a standalone CLI over one Python core
library; live CVE lookup via OSV.dev, never a local self-mutating DB;
red-flag ruleset improves via versioned human-reviewed releases; novel
attack patterns caught by a free static pass plus an opt-in LLM deep
scan; static scan always free, deep scan never automatic; traffic-light
plus humanized narrative output with JSON via flag; GitHub-only host in
v1 behind a pluggable interface; MIT and public from day one; primary
purpose ranked Leverage > Learning > Revenue.

Ran two independent councils. The 8-advisor `llm-council` found the
architecture sound but caught a real gap: the four scan pillars were all
designed around code-shaped threats, while 2026 research shows the
dominant attack on Claude Code skills is instruction-shaped — malicious
prose in `SKILL.md`. That produced DECISION 015 (distinct repo/skill
scan modes, with skill mode getting a default free instruction-content
pass) and DECISION 016 (deep scan must treat scanned content as
untrusted data, never as instructions). Both were added to CLAUDE.md's
non-negotiables. The `new-project` skill's 5-advisor council then
independently reached the same conclusion the first one had: validate
the mechanism before building more architecture around it.

**So the validation trace finally ran** — by hand, against
`github.com/browser-use/browser-use` (108k stars, real production repo
with real shipped skills). It confirmed the OSV.dev mechanism works
(`pillow==12.2.0` returned 26 real advisories; five other pinned
dependencies came back genuinely clean) and the install-hook check
produced a correct true negative. It also found two things neither
council caught: legitimate skills routinely instruct agents to fetch and
follow external URLs at runtime, which is structurally identical to the
attack vector RepoCheck exists to catch and cannot be resolved by a
one-time static scan (DECISION 020 — surfaced as an honest caveat, never
a pass/fail claim); and a concrete false-positive case, a secure
`printf … | auth login --api-key-stdin` pattern that a naive rule would
misflag as credential leakage.

Finally, rewrote MILESTONES.md from scratch — 12 milestones grouped
V1 / Hardening / Release, each with falsifiable acceptance criteria tied
to the actual `browser-use` results rather than to assumptions. V1 is
defined as M1–M8, ending at a CLI that vets a repo faster than doing it
by hand. DECISION 021 records the resequencing the councils argued for:
prove each mechanism against a real target first, extract the pluggable
interfaces from working code at M7 rather than designing them up front.

**Next session starts with:** M2, the walking skeleton — Python,
hardcoded to GitHub and OSV.dev, repo URL in and advisory list out, with
acceptance being that it reproduces this session's manual trace in code.
A stop-scoping trigger is recorded in MILESTONES.md M1: session 2 is
build-only, and OI-007 through OI-015 get resolved by the code that
needs them rather than in advance.

**Blockers:** none.

**Milestone status:** M1 DONE. M2–M12 NOT STARTED.

---

```
Close Verification:
- KNOWLEDGE.md updated: yes — entries: OSV.dev batch lookup validated with real data; manifest-only install-hook true negative; skills fetch-and-follow external URLs (TOCTOU gap); api-key-stdin false-positive case; GitHub hosted code-search API unreliable; gh CLI available and authenticated; session-discipline lesson that wip.md was never kept live
- DECISIONS.md updated: yes — entries: #001–#014 (session shape, cost model, output, host/ecosystem/provider scope, language), #015 (repo/skill scan modes), #016 (deep scan treats content as untrusted data), #017 (CLI is agent-agnostic), #018 (pluggable model provider), #019 (lightweight scaffold reaffirmed; purpose ranked Leverage > Learning > Revenue), #020 (dynamic external-fetch caveat), #021 (build resequencing)
- tasks/todo.md updated: yes — items closed: all 5 original scoping questions, 7 further scoping items, 5 technical open items, council review, new-project audit, validation trace, milestone rewrite — carried forward: M2 walking skeleton and its 3 acceptance criteria, plus .gitignore before first code commit
- Open Items table updated: yes — OIs touched: OI-001 through OI-006 CLOSED with resolutions; OI-007, OI-008, OI-009, OI-010, OI-015 OPEN; OI-011, OI-012, OI-013, OI-014 PENDING (deferred from Socratic challenge, not blocking)
- tasks/codebase_map.md updated: yes — entries: LICENSE and council-transcript-20260807T000000.md were missing from the map and have been added; no mapped-but-deleted entries; .gitignore noted as not yet existing
- tasks/wip.md reset to empty template: yes — but see KNOWLEDGE.md: it was empty all session, not kept live, which is a discipline miss to correct in session 2
- git commit created: [filled below]
- git push completed: [filled below]
- git worktree audit: [filled below]
```
