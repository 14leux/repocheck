# DECISIONS.md

## DECISION 001 — Live lookup, not self-mutating local threat DB

**Date:** 2026-08-07 (originally proposed 2026-08-04 in the originating
`oracle_aura` conversation, reconfirmed here)

**Context:** Original framing was "a repo that checks and updates
itself on the newest threats." That implies a maintained local feed and
a scheduled job, which silently goes stale the moment the job breaks —
a failure class already hit in `oracle_aura` (Lessons 81/82/87: something
reports success while quietly doing nothing).

**Decision:** RepoCheck queries live sources (OSV.dev, GitHub Security
Advisories, npm/PyPI/PyPA advisory feeds) at the moment of each scan.
No local vulnerability database to go stale.

**Rejected alternatives:** Self-mutating local DB with a scheduled
refresh job — rejected because staleness is invisible until someone
gets a false "clean" verdict on a repo with a known CVE.

**Tradeoffs:** Slower per-scan (network calls to multiple sources
instead of a local index), and scan quality depends on those sources'
uptime/rate limits. Accepted because correctness > speed for a security
tool, and the failure mode (a slow scan) is far less dangerous than the
failure mode it avoids (a silently stale "safe" verdict).

**Implications:** Core scan library needs a pluggable "source" layer
per advisory feed, with graceful degradation (partial result + a
flagged "source X unreachable" note) rather than a hard failure when
one feed is down.

---

## DECISION 002 — Ship as both a Claude Code skill and a standalone CLI, sharing one core library

**Date:** 2026-08-07

**Context:** First-session scoping question: skill-only vs. standalone
CLI/service. Skill-only is fastest to something usable by Mailu
personally; standalone CLI reaches non-Claude-Code users but adds
packaging/plumbing before any scan logic exists.

**Decision:** Build the scan logic as a standalone core library first,
with a thin skill wrapper and a thin CLI wrapper on top of it from day
one. Neither wrapper contains scan logic itself.

**Rejected alternatives:**
- Skill-only — rejected because the user wants this to eventually be a
  public tool usable outside Claude Code, and retrofitting a CLI onto
  skill-shaped code later is more work than designing the interface
  cleanly once.
- Standalone-only — rejected because it delays a usable-by-Mailu
  version behind CLI packaging work that doesn't advance the actual
  scan quality.

**Tradeoffs:** More upfront interface design discipline required (the
core library's API must not assume it's being called from either
wrapper). Slightly slower to first usable output than skill-only.

**Implications:** OI-002 (language/runtime choice) must support both a
Claude Code skill (which typically shells out or runs as a script) and
a standalone CLI cleanly — this constrains the choice.

---

## DECISION 003 — v1 scope: CVEs + code red flags + dependency freshness + plain-language verdict

**Date:** 2026-08-07

**Context:** README originally suggested starting narrower (CVEs + a
short red-flag list only). User chose the fuller README scope instead
when asked directly.

**Decision:** First working version covers all four pieces from the
README's "What it's for" section: known CVEs in declared dependencies,
code-level red flags (obfuscation, suspicious network calls, credential
harvesting patterns, install-time scripts), a dependency-freshness
signal, and a plain-language verdict tying it together.

**Rejected alternatives:** CVE-only v1 — rejected by user as too narrow
to be useful (misses the code-level red flags that motivated this
project in the first place, per the PixelRAG review that inspired it).

**Tradeoffs:** More surface area before anything ships; each of the
four pieces needs its own design pass (data source, detection method,
scoring) before v1 is "done." Accept the risk of a longer path to first
shippable version in exchange for a v1 that's actually useful for the
PixelRAG-style review this was born from.

**Implications:** MILESTONES.md should probably break these four into
separate milestones rather than one big "build v1" milestone, so partial
progress is visible and each piece can be validated independently.

---

## DECISION 004 — Lightweight PROJECT_DISCIPLINE.md subset for now

**Date:** 2026-08-07

**Context:** Day one, nothing built yet, no live infra, no external
users — the exact condition PROJECT_DISCIPLINE.md §10 names as the
signal to stay lightweight.

**Decision:** Adopt the lightweight subset: CLAUDE.md,
`.agent/instructions.md` (boot + close + Open Items combined, not split
into session_start.md/session_close.md yet), `tasks/context.md`,
`tasks/wip.md`, `tasks/todo.md`, `tasks/codebase_map.md`,
`MILESTONES.md`, `KNOWLEDGE.md`, `DECISIONS.md`. No `IMPROVEMENTS.md`,
no strict OI verification protocol, no acceptance-tests gate.

**Rejected alternatives:** Full apparatus — rejected per §10's own
guidance; would produce placeholder content (e.g. an acceptance-tests
gate with no tests yet) that erodes trust in the docs.

**Tradeoffs:** Will need to add IMPROVEMENTS.md and a stricter
verification protocol once RepoCheck has live infra (e.g. a hosted
scan endpoint) or external users — revisit then, not before.

**Implications:** Keep `.agent/instructions.md` as a single file until
it grows past the point of easy scanning (§10's stated trigger for
splitting into `.agent/workflows/`).

---

## DECISION 005 — MIT license, public repo from day one

**Date:** 2026-08-07

**Context:** Public-repo plan was an open scoping question (README
"Scope for the first real session" #4).

**Decision:** MIT license. Repo goes public immediately rather than
staying private until a "usable by Mailu" milestone.

**Rejected alternatives:** Private-until-milestone — rejected by user;
public-from-day-one avoids managing a separate private→public
transition later.

**Tradeoffs:** Unfinished/early-stage code is visible publicly from the
start. Accepted — this is dev tooling aimed at other developers who are
used to seeing early-stage open-source repos.

**Implications:** Needs a `LICENSE` file (MIT) and a real
`.gitignore` before the first push of any real code, and commit
messages/README framing should assume a public audience from now on.

---

## DECISION 006 — Amendment to Decision 001: red-flag ruleset may evolve via versioned releases (not live self-mutation)

**Date:** 2026-08-07

**Context:** User wants RepoCheck to "learn" over time, especially from
common security lapses it encounters, given how fast agentic-coding-era
attackers invent new techniques. Decision 001 rejected a
self-mutating local threat database because an unattended scheduled
job that silently breaks produces a false "safe" verdict — but that
concern is specifically about *live, unattended, production
self-mutation*, not about the tool improving at all.

**Decision:** The CVE/advisory lookup stays exactly as Decision 001
specified — live query at scan time, never a local DB. Separately, the
**red-flag pattern ruleset** (the static checklist) is allowed to
improve over time, but only through normal versioned software
releases: a human reviews and merges new/updated rules, same as
updating ESLint or Semgrep rules. Never an autonomous live feed the
tool rewrites itself from mid-scan or on a schedule.

**Rejected alternatives:** A live-updating ruleset fed by some external
threat feed — rejected for the same reason as the original Decision
001: silent staleness risk, now applied to the ruleset instead of just
the CVE data.

**Tradeoffs:** The ruleset can lag behind brand-new attack techniques
between releases. This gap is why Decision 007 (LLM reasoning pass)
exists — it's the mechanism that catches what the versioned ruleset
hasn't caught up to yet.

**Implications:** Needs a lightweight internal process later (not v1
priority) for turning a deep-scan finding that isn't in the ruleset yet
into a reviewed, committed rule for a future release.

---

## DECISION 007 — Novel attack pattern detection: static ruleset + opt-in targeted LLM reasoning pass ("deep scan")

**Date:** 2026-08-07

**Context:** A static checklist only ever catches patterns someone
already wrote a rule for. Given how quickly agentic-coding-era
attackers can invent new supply-chain/malicious-code techniques, v1
needs some ability to catch a pattern nobody has documented yet — pure
pattern-matching can't do that by definition.

**Decision:** Two-tier detection:
1. **Static pass** (default, runs on every scan) — regex/AST checklist
   across all files. Fast, free, scales to any repo size, catches known
   patterns.
2. **Deep scan** (opt-in, not automatic) — a targeted LLM reasoning
   pass over high-risk files only: anything the static pass flagged as
   borderline, plus install/postinstall scripts and files touching
   `eval`/`exec`/network calls/env vars/base64 decoding. Because it's
   reasoning about behavior rather than matching a fixed pattern, it
   can catch techniques not yet in the ruleset.

**Rejected alternatives:** LLM reasoning over the entire repo by
default — rejected as both a cost problem (Decision 008) and a
scale problem (doesn't work on very large repos without either huge
cost or context-window limits).

**Tradeoffs:** Deep scan won't run unless the user opts in, so a
user who only ever runs the static default could still miss a novel
technique. Accepted because the alternative (always-on deep scan) makes
every scan slow and costly by default, which would suppress usage more
than it protects.

**Implications:** The static pass's flagging logic effectively decides
what deep scan even looks at — its "borderline" thresholds matter and
should be revisited if deep scan turns out to be looking at the wrong
things in practice.

---

## DECISION 008 — Cost model: static scan is free by default, deep scan is opt-in and costs tokens/API usage

**Date:** 2026-08-07

**Context:** RepoCheck runs in two contexts — a standalone CLI and a
Claude Code skill — and the LLM reasoning pass (Decision 007) has a
real cost in either context. Users need to know upfront what a scan
will cost before running it, not discover it afterward.

**Decision:**
- **Static scan** (manifest parsing, red-flag checklist, live CVE
  lookups against free public sources) costs nothing — no LLM call
  involved at all. This is the default for both CLI and skill.
- **Deep scan** is opt-in only (e.g. a `--deep` flag or an explicit
  "run deep scan" step), never automatic. Cost depends on invocation:
  as the standalone CLI it uses the user's own Anthropic API key and
  bills at standard API rates; as the Claude Code skill it consumes the
  user's Claude Code usage for that session, like any other agentic
  task.

**Rejected alternatives:** Deep scan always-on — rejected per Decision
007's tradeoffs (cost/scale). Static-only forever — rejected because it
can't address Decision 007's stated goal of catching novel patterns.

**Tradeoffs:** Requires the CLI to have some way to accept/configure an
API key for deep-scan mode, which is extra setup surface the static-only
path doesn't need.

**Implications:** Output UX (Decision 009) must tell the user the cost
and time implications *before* deep scan runs, not just report results
after the fact.

---

## DECISION 009 — Output must be humanized and set expectations upfront (what's scanned, cost, time)

**Date:** 2026-08-07

**Context:** The intended audience includes non-experts ("vibecoders")
who may not know what a CVE or a supply-chain attack even is. A bare
safe/unsafe verdict or a raw CVE dump doesn't serve that audience, and
silently running a paid deep scan without telling the user what it
costs or roughly how long it takes is a bad default.

**Decision:** Two humanized-language touchpoints, not just one:
1. **Before running** — plain-language explanation of what static scan
   does (free, fast) and, if anything gets flagged, what deep scan would
   add, what it costs, and a rough time estimate — so the user opts in
   with real numbers, not a guess.
2. **After running** — every finding explained in plain language: what
   the pattern is, why it's risky, and what a real-world attack using it
   looks like, so a scan doubles as a small security lesson rather than
   just a gate.

Time estimates: static scan gets a rough upfront estimate from a cheap
pre-flight (file count, declared-dependency count) before the real scan
starts. Deep scan can only be estimated *after* the static pass
completes, based on how many files it actually flagged — repo size
alone doesn't predict deep-scan time, flagged-file count does.

**Rejected alternatives:** Exact time promises — rejected as
undeliverable given dependence on live API latency and, for deep scan,
on how much gets flagged rather than repo size.

**Tradeoffs:** Estimates are ranges, not guarantees — acceptable since
the goal is informed consent before a cost is incurred, not precision.

**Implications:** The verdict/report format (still not fully designed)
needs a distinct "pre-flight" summary state separate from the final
report, and needs per-finding explanatory copy, not just a
pattern-name-and-severity table.

---

## DECISION 010 — Core library language: Python

**Date:** 2026-08-07

**Context:** OI-002. The core library's language constrains
distribution, skill/CLI integration, and how much ecosystem tooling is
available for manifest parsing, static analysis, and API calls.

**Decision:** Python.

**Rejected alternatives:**
- **Node/TypeScript** — natural fit with Claude Code's own ecosystem
  and trivial npm distribution, but weaker for analyzing non-JS
  languages' code and an odd fit given npm is itself one of the
  ecosystems being scanned.
- **Go** — best-in-class single-binary distribution, but smaller
  ecosystem for the fast, varied parsing work this needs (many manifest
  formats, AST inspection, API glue), slower to prototype.

**Tradeoffs:** Weaker CLI distribution story than Go (users need Python
installed; packaging/dependency issues are historically messier) and
slower startup time as a CLI. Accepted because OSV.dev has an official
Python client, Python's parsing/AST ecosystem is the most mature fit for
what RepoCheck actually does, and prototyping speed matters most right
now with nothing built yet. Distribution pain can be mitigated later
(`pipx`, a compiled distribution via PyInstaller) once the core is
proven — not a v1 blocker.

**Implications:** Core library, CLI wrapper, and any deep-scan
orchestration are Python. Skill wrapper calls into it (as a script or
imported module — exact mechanism still open, see OI-002 follow-up in
Milestone #2).

---

## DECISION 011 — Primary CVE/advisory source: OSV.dev

**Date:** 2026-08-07

**Context:** OI-003. Decision 001 commits to live lookup, but the
actual source needs to be chosen concretely — coverage, auth
requirements, and rate limits differ a lot between candidates.

**Decision:** OSV.dev as the primary/default source for v1. It
aggregates npm, PyPI, Go, crates.io, Maven, RubyGems, and more under one
API, is free, requires no auth, has generous rate limits, and has a
batch-query endpoint for repos with many dependencies.

**Rejected alternatives:**
- **GitHub Security Advisories (GHSA)** as primary — GitHub-native and
  sometimes faster to list an advisory, but requires a token for
  reasonable rate limits and is GitHub-specific, working against the
  ecosystem/host-agnostic goal. Kept as a possible secondary enrichment
  source later, not a v1 requirement.
- **Ecosystem-native feeds** (npm audit, PyPA advisory DB, RustSec,
  etc.) as primary — most authoritative per-ecosystem, but one
  integration per ecosystem, directly working against staying
  agnostic with minimal integration surface.

**Tradeoffs:** OSV.dev is an aggregator, so its data is only as fresh as
what it ingests from upstream — usually fast, but not instantaneous.
Accepted as a reasonable tradeoff for single-integration ecosystem
breadth.

**Implications:** Directly reduces the scope of OI-004's ecosystem
question — picking OSV.dev covers most ecosystem breadth "for free"
without a per-ecosystem integration.

---

## DECISION 012 — v1 host/ecosystem scope: GitHub-only host, pluggable interface; ecosystem breadth via OSV.dev

**Date:** 2026-08-07

**Context:** OI-004, the concrete version of the "must be
platform-agnostic" requirement. Fully agnostic on day one (every git
host, every ecosystem, all tested) is a lot of surface area before
anything ships end-to-end.

**Decision:** Build the file-access layer as an interface with
**GitHub as the only implementation in v1** — best API for cheaply
listing/reading files without a full clone. Ecosystem breadth comes
from Decision 011 (OSV.dev) rather than a separate per-ecosystem
integration, so "ecosystem-agnostic" is substantially satisfied without
extra v1 work. GitLab/Bitbucket/self-hosted git adapters are explicitly
post-v1, added behind the same interface once the core is proven.

**Rejected alternatives:**
- **Multi-host from day one** — actually meets "agnostic" immediately,
  rejected as too much integration work (each host has a different API
  shape) before the core scan logic itself is validated.
- **Git-clone-only, no host API at all** — most genuinely
  host-agnostic (works on any git host including self-hosted), rejected
  because it loses the efficiency win of host APIs for very large repos
  (can't cheaply list just manifest files without a full clone).

**Tradeoffs:** v1 literally cannot scan a GitLab- or Bitbucket-hosted
repo. Accepted as an explicit, named scope limit rather than silently
under-delivering on "agnostic" — the architecture is agnostic-ready
(interface-based), the v1 implementation is not yet agnostic-complete.

**Implications:** Milestone #2 (core library skeleton) should define
this file-access interface even though only one implementation exists
at first, so adding GitLab/Bitbucket later doesn't require a rewrite.

---

## DECISION 013 — Verdict format: traffic-light + narrative, JSON available via flag

**Date:** 2026-08-07

**Context:** OI-005. Decision 009 already committed to humanized
output; this decides the concrete shape it takes.

**Decision:** Primary human-facing output is a traffic-light signal
(e.g. clear/caution/danger) paired with a plain-language narrative per
Decision 009. A structured `--json` output is available for anyone
piping results into CI or other tooling. Underneath both, a real
severity model combines CVE severity (CVSS), red-flag pattern risk
level, and dependency freshness lag into one signal — not yet designed
in detail.

**Rejected alternatives:**
- **Single score/grade (0–100 or A–F)** — instantly skimmable and easy
  to compare repos, rejected because it risks feeling like a black box
  ("why did I get a C?") and can mask a single severe finding (e.g. a
  live credential-harvesting script) behind an average-looking number.
- **Structured findings list only (linter-style)** — most
  information-dense and easiest to pipe into other tooling on its own,
  rejected as the sole output because it doesn't meet the
  "teach vibecoders" goal without a narrative layer on top anyway.

**Tradeoffs:** Traffic-light + narrative is less instantly skimmable
across many repos at once than a bare score. Accepted because the
stated goal (educate, not just gate) outweighs at-a-glance
comparability for v1's target user.

**Implications:** The severity-weighting model (how CVSS + red-flag
risk + freshness combine into one traffic-light color) is real design
work still owed, separate from just picking the output format —
tracked as follow-up under Milestone #6 (plain-language verdict).

---

## DECISION 014 — CLI deep-scan API key via environment variable only

**Date:** 2026-08-07

**Context:** OI-006. The standalone CLI's opt-in deep scan (Decision
007/008) needs the user's own Anthropic API key. As a security tool,
how RepoCheck itself handles that secret is scrutinized more than it
would be for an unrelated tool.

**Decision:** `ANTHROPIC_API_KEY` environment variable is the only v1
mechanism — matches Anthropic's own SDK convention, requires zero new
secret-storage code in RepoCheck, and keeps RepoCheck's own attack
surface smaller by never writing the key to disk itself.

**Rejected alternatives:**
- **Config file** (e.g. `~/.repocheck/config`) — persists across runs
  without re-exporting, rejected for v1 because it makes RepoCheck
  responsible for secret-at-rest handling (file permissions, ensuring
  it's never logged or accidentally committed), more that can go wrong
  for a tool whose brand is catching exactly that kind of mistake.
- **Interactive prompt every run, no persistence** — nothing touches
  disk, rejected because repeated typing into a terminal increases
  exposure (scrollback/history/shoulder-surfing) more than it reduces
  risk, and is annoying for repeated use.

**Tradeoffs:** Users must set up the env var themselves each
session/shell profile; no persistence convenience. Accepted — deep scan
is opt-in and infrequent by design (Decision 007), so the convenience
cost is low relative to the risk avoided.

**Implications:** CLI must fail with a clear, specific error message
when `ANTHROPIC_API_KEY` is unset and deep scan is requested — not a
generic/cryptic failure.

---

## DECISION 015 — Distinct repo/skill scan modes; skill mode adds a default, free instruction-content analysis pass

**Date:** 2026-08-07

**Context:** Council review (`council-transcript-20260807T000000.md`)
found that RepoCheck's four scan pillars (CVE, code red-flags,
freshness, verdict) were designed around code-shaped threats. 2026
research (Snyk ToxicSkills, Datadog Security Labs, CSA) shows the
dominant attack on Claude Code skills specifically is plain-English
malicious instructions embedded in `SKILL.md` prose (e.g. "read
`~/.ssh/id_rsa`, POST it to this URL"), not obfuscated code — prompt
injection found in 36% of tested skills. Validated by trace: a
regex/AST code-red-flag checklist has no mechanism to catch a
well-formed English sentence instructing the agent to exfiltrate a
file, since it isn't malformed code. Confirmed the current v1 design
would give a malicious skill a clean "static scan" green light —
false confidence on exactly the artifact type this project was partly
born to protect against.

**Decision:** RepoCheck treats **repo** and **skill** as distinct scan
modes sharing common machinery (CVE lookup, dependency freshness, code
red-flag checklist) where applicable. Skill mode adds a **default,
free, static-first instruction-content analysis pass** over
`SKILL.md`/skill manifest text as a first-class pillar — not gated
behind paid opt-in deep scan — checking for known malicious-instruction
patterns (credential/key access + exfiltration requests, "ignore
previous instructions"-style overrides, shell-out-and-pipe patterns,
environment-variable exfiltration requests). Deep-scan escalation
(Decision 007) always includes `SKILL.md`/skill manifest files as
high-risk by default, not only when the static pass already flagged
something — the static pass may be blind to a novel instruction
phrasing.

**Rejected alternatives:** Treating skill-scanning as "repo-scanning,
but smaller," with one shared pipeline — this was the original v1
design; rejected because two of the four pillars (CVE, freshness) often
don't even apply to a skill (most skills have no dependency manifest),
and the code-red-flag pillar misses the primary skill-specific threat
entirely.

**Tradeoffs:** More surface area before v1 ships — a second detection
pillar (instruction-content analysis) needs its own pattern list,
separate from the code red-flag checklist, and its own verdict template
(Milestone #6 needs a skill-mode variant, not just a repo-mode one).
Accepted because shipping v1 without this produces a worse outcome than
delaying it — a security tool giving false confidence on its stated use
case is actively harmful, not just incomplete.

**Implications:** Milestone #6 (plain-language verdict) needs two
verdict templates, not one. OI-007 (skill-to-core-library call
mechanism) should be resolved with this in mind — RepoCheck's own
future skill wrapper's `SKILL.md` becomes a file worth scanning on its
own releases (dogfooding, deferred to post-v1 per the council's
priority filter).

---

## DECISION 016 — Deep-scan LLM pass must treat scanned content as untrusted data, never as instructions

**Date:** 2026-08-07

**Context:** Council peer review (Pass 2) surfaced that RepoCheck's own
deep-scan LLM pass (Decision 007) reads repo/skill text into an LLM's
context to reason about it. If that text contains an injected
instruction (the exact attack Decision 015 exists to catch), the
injected instruction is now inside the reasoning model's context during
analysis — RepoCheck's own scanner becomes attackable by the thing it's
scanning. This applies to both repo mode (a malicious README, CI
config, or code comment) and skill mode (a malicious `SKILL.md`), so
it's mode-agnostic, not specific to Decision 015.

**Decision:** The deep-scan implementation must structurally delimit
all scanned content as untrusted data (e.g. clearly fenced/tagged input
that the reasoning prompt explicitly frames as "content to analyze,"
never as "instructions to follow"), regardless of scan mode. This is a
non-negotiable design requirement for Milestone #2's core library, not
an implementation detail to sort out later.

**Rejected alternatives:** None seriously considered — this is a
correctness requirement for any tool that feeds untrusted external text
into an LLM context, not a tradeoff with a defensible alternative.

**Tradeoffs:** None meaningful — this is closer to "do it correctly"
than a design choice with competing costs.

**Implications:** Added to CLAUDE.md's non-negotiables list alongside
"never execute untrusted code" and "live lookup, not self-mutating
local DB." Core library's deep-scan interface (Milestone #2) must be
designed with this constraint from the start, not retrofitted.

---

## DECISION 017 — CLI is inherently agent-agnostic; other coding-agent integrations follow the same thin-wrapper pattern

**Date:** 2026-08-07

**Context:** User asked whether RepoCheck can be used with other coding
agents (e.g. Codex, Antigravity), not just Claude Code.

**Decision:** The standalone CLI (Decision 002) is already agent-agnostic
by construction — it's an ordinary command-line program, callable by any
agent (or human) capable of running a shell command, with no Claude Code
dependency. This needs no new work to be true; it falls directly out of
the core-library-plus-thin-wrapper architecture already decided. If a
given coding agent has its own native extension format (the way Claude
Code has skills), a dedicated wrapper for that format can be added later
behind the same core library — the same pattern already used for the
Claude Code skill wrapper (Decision 002) and the git-host pluggable
interface (Decision 012). No such agent-specific wrapper beyond the
Claude Code skill is in v1 scope; the CLI is what makes RepoCheck usable
with any other agent today.

**Rejected alternatives:** Building bespoke integrations for every
coding agent's native format up front — rejected as unnecessary v1 work
given the CLI already serves that need generically, and premature given
no specific demand signal for any one platform's native format yet.

**Tradeoffs:** Users of agents with native extension/plugin formats
(Codex, Antigravity, etc.) get a slightly less integrated experience via
CLI shell-out than a purpose-built native wrapper would offer. Accepted —
same tradeoff already accepted for GitLab/Bitbucket in Decision 012,
consistent with "prove the core first, add native integrations once
there's real demand."

**Implications:** None for Milestone #2 — the core library and CLI
wrapper already satisfy this by design. Revisit only if a specific
agent platform's native format becomes a real, named demand.

---

## DECISION 018 — Amendment to Decision 014: deep-scan model provider is a pluggable interface, Anthropic-only implementation in v1

**Date:** 2026-08-07

**Context:** Decision 014 locked the CLI's deep-scan auth to
`ANTHROPIC_API_KEY` with no discussion of supporting other model
providers. That's inconsistent with every other agnosticism call made
this session — git host (012), dependency ecosystem (011), coding
agent (017) — all of which are designed as pluggable interfaces with
one v1 implementation, not permanently locked to one vendor. Note this
question only applies to the **standalone CLI** path — in skill mode,
deep scan runs on the existing Claude Code session with no separate
provider choice involved.

**Decision:** The deep-scan model-calling layer in the core library is
a pluggable interface (a "model provider" abstraction), with
**Anthropic as the only implementation shipped in v1** — fastest to
build, matches where RepoCheck originates. Other providers (OpenAI,
Gemini, etc.) can be added behind the same interface later without a
rewrite, each with their own provider-specific env var
(`OPENAI_API_KEY`, etc.) following the same environment-variable-only
pattern from Decision 014.

**Rejected alternatives:**
- **Anthropic-only, no pluggable interface** (original Decision 014
  scope) — rejected as inconsistent with the agnostic pattern applied
  everywhere else, and would require a real rewrite (not just an
  addition) to support another provider later.
- **Multiple providers supported in v1 itself** — rejected as
  unnecessary v1 scope; each additional provider means writing/tuning
  the deep-scan reasoning prompt against a different model's quirks
  with no confirmed demand yet for a second provider.

**Tradeoffs:** None meaningful for v1 scope — designing the interface
to be pluggable from the start costs little extra now and avoids a
rewrite later, the same tradeoff already accepted in Decisions 011,
012, and 017.

**Implications:** Milestone #2's core library must define the model-
provider interface (not just call the Anthropic SDK directly inline)
even though only one implementation exists in v1 — same discipline as
Decision 012's file-access interface.

---

## DECISION 019 — Discipline scaffold level reaffirmed lightweight; primary purpose classified as Leverage > Learning > Revenue

**Date:** 2026-08-07

**Context:** Ran the `new-project` skill (Spec Mode, using README.md +
DECISIONS.md as the input spec) to audit discipline coverage. Its
mandatory greenfield scaffold is heavier than Decision 004's chosen
lightweight `PROJECT_DISCIPLINE.md` §10 subset — it requires separate
`session_start.md`/`session_close.md`/`verification.md`/`bug_fixing.md`
pointer files plus a `.claude/settings.json` UserPromptSubmit hook that
force-injects the boot directive every session. Per discipline rule (a
conflicting instruction gets flagged, not silently applied), this was
surfaced to the user rather than adopted by default. Separately,
`new-project`'s template requires a primary-purpose classification
(revenue / leverage / learning) that RepoCheck never had stated
explicitly.

**Decision:**
- **Scaffold level:** stays lightweight, per Decision 004 — unchanged.
  The four extra pointer files and the enforcement hook are explicitly
  not adopted. Content gaps `new-project`'s template surfaced that are
  genuinely useful (glossary, purpose classification, consolidated
  architecture overview, session-by-session build table) get folded
  into the existing lightweight file set instead of adding new files.
- **Primary purpose:** ranked **Leverage first, Learning second, Revenue
  third** — not a single exclusive purpose, but a stated priority order.
  RepoCheck exists first to serve Mailu's own need (protecting personal/
  project work, the `oracle_aura` origin case), second to build security-
  tooling/agent-safety capability, and only third as a potential future
  revenue vehicle (MIT/public-from-day-one per Decision 005 keeps that
  door open without committing to it now).

**Rejected alternatives:** Adopting `new-project`'s full scaffold
now — rejected as premature per §10's own trigger (no live infra, no
external users yet); would produce the "placeholder content that
erodes trust" §10 warns against for a project with no code written yet.

**Tradeoffs:** None significant — this reaffirms an existing decision
rather than changing course, and purpose classification costs nothing
to state now that it wasn't already implicitly true from the README.

**Implications:** Priority filter for future scoping/council sessions
should default to Leverage → Learning → Revenue ordering (mirrors the
llm-council skill's own default ordering for Mailu's ventures) unless a
specific session states otherwise. Glossary, purpose framing, and a
consolidated architecture overview should be added to README.md/
CLAUDE.md as content, not as new discipline files.

---

## DECISION 020 — Dynamic external-content fetch-and-follow is a distinct, honestly-caveated risk category in skill mode

**Date:** 2026-08-07

**Context:** Manual validation trace against a real repo
(`browser-use/browser-use`, see KNOWLEDGE.md) found that its legitimate,
popular skill (`skills/browser-use/SKILL.md`) routinely instructs the
agent to fetch and read external URLs at runtime for setup/mechanics
detail. This is a normal progressive-disclosure design pattern, not
malicious — but it is structurally identical to the primary attack
vector Decision 015 was written to catch: content fetched dynamically
at use-time is not the content RepoCheck scans at review-time, a
time-of-check/time-of-use (TOCTOU) gap no one-time static content scan
can close, since the linked content can change after the scan runs.

**Decision:** Skill-mode instruction-content analysis (Decision 015)
adds "instructs the agent to fetch and follow external content at
runtime" as its own named risk factor, surfaced honestly in the
verdict as an unresolvable-by-scanning caveat ("this skill dynamically
fetches and follows external content, which RepoCheck cannot verify at
scan time — safety of this skill partly depends on trusting the linked
domain(s) to never serve something different later"), never resolved to
a clean pass/fail claim, and never treated as inherently malicious on
its own — the browser-use case proves it is common in normal, safe
skills. Where the linked content is same-repo or same-org, resolving
and scanning it too is worth attempting; where it points to a
third-party domain, RepoCheck names the domain and stops there rather
than pretending to verify content it cannot control.

**Rejected alternatives:**
- **Flag dynamic external fetches as a red flag/negative signal** —
  rejected because the validation trace proved this pattern is common
  in entirely legitimate, popular skills; treating it as inherently
  suspicious would produce constant false positives on normal skills.
- **Ignore the pattern entirely (out of scope)** — rejected because it
  is exactly the mechanism the 2026 research identifies as bypassing
  model-level defenses ("dynamic context commands run before the model
  sees the skill at all"); silently not mentioning it would misstate
  what RepoCheck's scan can and cannot guarantee.

**Tradeoffs:** Adds a fourth thing skill-mode verdicts must communicate
(alongside CVE-adjacent findings, code/instruction red flags, and
freshness) — a caveat rather than a finding, which the humanized-output
design (Decision 009) needs to express without reading as alarmist on
an otherwise-clean skill.

**Implications:** Skill-mode verdict template (OI-010) must have a
distinct slot for "unverifiable-by-scanning" caveats, separate from
pass/fail findings. Confirms Decision 015's instruction-content pattern
list (OI-009) needs a distinct pattern category for "fetch external URL
and follow as instruction," not lumped with credential-exfiltration
phrasings — the two have very different true/false-positive profiles.

---

## DECISION 021 — Build sequencing: prove mechanisms first, extract interfaces from working code

**Date:** 2026-08-07

**Context:** Decisions 012 and 018 each carry an implication line saying
Milestone #2 (core library skeleton) must *define* the pluggable
file-access and model-provider interfaces up front. The `new-project`
council's Executor advisor argued the opposite ordering, and the
chairman sided with it: build a crude hardcoded path against a real
target first, extract the interfaces from working code afterward. The
reasoning that decided it — every interface in the plan currently wraps
a detection mechanism that had never been run once, and polishing
abstractions around an unproven mechanism is expensive to unwind if the
mechanism turns out wrong. The M1 validation trace then demonstrated
this concretely: running the mechanism for 20 minutes surfaced a risk
category (DECISION 020) that would have invalidated part of an
interface designed in advance.

**Decision:** Interfaces still exist and are still required — Decisions
012 and 018 stand. Only their *sequencing* changes. The walking
skeleton (M2) is hardcoded to GitHub and OSV.dev with no abstraction;
the interfaces are extracted in M7, after M2–M6 work against real
targets, with M7's acceptance criteria requiring that all earlier
criteria still pass post-refactor.

**Rejected alternatives:**
- **Define interfaces in M2 as originally implied** — rejected because
  it designs abstraction boundaries before knowing what varies, which
  is how interfaces end up shaped around assumptions rather than around
  real usage.
- **Skip the interfaces entirely** (the council's First Principles
  advisor's stronger position) — rejected; the chairman explicitly did
  not side with this. Retrofitting a second git host or model provider
  without an interface is a genuine rewrite, and defining one thin
  interface over working code is cheap.

**Tradeoffs:** M2–M6 will contain code that M7 then refactors, which
looks like rework. Accepted — it is cheaper to extract an interface
from three working call sites than to guess its shape before any exist.

**Implications:** Supersedes the sequencing guidance in Decisions 012
and 018 (not their substance). MILESTONES.md reflects the new order.
Session 2 starts with M2 code, not further design — the stop-scoping
trigger recorded in M1.

---

## DECISION 022 — Amendment to Decision 005: repository starts private, goes public at M12

**Date:** 2026-08-07

**Context:** Decision 005 committed to MIT licence and a public
repository from day one. At session 1 close it emerged that no git
remote had ever been created — the entire session's work existed on one
disk. Resolving that forced the public-vs-private question earlier and
more concretely than Decision 005 had considered it: the choice was no
longer abstract ("should this be public eventually") but immediate
("does this specific commit go public right now").

**Decision:** The repository is created **private**
(`github.com/14leux/repocheck`) and flips to public at M12 (public
release polish). The MIT licence is unchanged and already committed —
only the timing of publication moves. Durability is satisfied
immediately: the work is off this machine and recoverable regardless of
visibility.

**Rejected alternatives:**
- **Public immediately, per Decision 005's letter** — rejected because
  what exists today is scoping documentation and a decision log, not a
  working tool; publishing a security tool's full reasoning before it
  can scan anything invites evaluation against a standard it does not
  yet claim to meet.
- **Stay local-only, defer the remote to session 2** — rejected
  outright; it leaves several hours of work on a single disk for no
  benefit, and the durability rule exists precisely to prevent this.

**Tradeoffs:** Loses the "build in public from the start" benefit
Decision 005 implied — early contributors cannot find the project, and
the decision history is not visible as it forms. Accepted as small:
there is nothing yet for a contributor to contribute to, and M12 already
exists as the natural publication gate.

**Implications:** M12's acceptance criteria gain one item — flip the
repository to public. Decision 005 stands on licence and on the
intent to be public; only its timing is superseded here. Default branch
is currently `master`; whether to rename to `main` before publication is
worth settling at M12.

---

## DECISION 023 — Resolves OI-007: skill call mechanism is "shell out to the CLI," deep scan runs on the session directly

**Date:** 2026-08-07

**Context:** OI-007 (open since session 1): how does the Claude Code
skill wrapper actually invoke the core scan logic — shell out to a
script, or import the library as a module? M8's CLI (`repocheck.py`)
already existed and worked standalone by the time M10 started.

**Decision:** The skill wrapper is `skills/repocheck/SKILL.md` itself —
in Claude Code, a skill fundamentally *is* a markdown instruction file,
not a code module, so "the wrapper" is the instructions telling the
agent how to invoke `repocheck.py` via the Bash tool for the static
scan. For the opt-in deeper review, the skill instructs the agent to
list high-risk files via `deep_scan.py` *without* `--confirm` (no API
call), then read and reason about those files directly in its own
session — never shelling out to `deep_scan.py --confirm`, which is the
standalone-CLI path requiring the user's own `ANTHROPIC_API_KEY`
(Decisions 008/018). This satisfies M10's "deep scan runs on the
session rather than requiring a separate key" criterion structurally,
not just by convention.

**Rejected alternatives:**
- **Import the core library as a Python module directly in-session** —
  rejected; Claude Code sessions interact with the filesystem/shell via
  tools, not by importing arbitrary project code into the agent's own
  runtime, so this doesn't match how skills actually execute.
- **Skill shells out to `deep_scan.py --confirm` for deeper review** —
  rejected; would require the user to hold a separate Anthropic API key
  even when already inside a paid Claude Code session, double-charging
  conceptually and contradicting Decision 008's cost model.

**Tradeoffs:** The skill's "deeper review" instructions duplicate some
of `deep_scan.py`'s reasoning discipline (untrusted-content handling,
injection-attempt-as-finding) in prose rather than calling shared code
directly — acceptable, since a skill's actual code path is bash calls
and file reads, not Python imports, so some duplication between
`SYSTEM_PROMPT` in `deep_scan.py` and `SKILL.md`'s prose is structural,
not an oversight.

**Implications:** `skills/repocheck/SKILL.md` is RepoCheck's real skill
manifest going forward — any change to the CLI's invocation (flags,
output format) needs a corresponding check that the skill's
instructions still match. Confirmed clean under RepoCheck's own
instruction-scan (dogfooding, M10) — see KNOWLEDGE.md for a real false
positive this surfaced and fixed in `skill_scan.py` itself.
