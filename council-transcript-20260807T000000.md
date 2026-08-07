# Council Transcript — RepoCheck v1 Scope Pressure-Test

**Date:** 2026-08-07

## Original Question

Run the council on the RepoCheck v1 plan and all locked-in scoping
decisions to ensure it's a good v1.

## Step 0 — Context Scan

Full session context already in hand: README.md, DECISIONS.md (14
entries, #001–#014), MILESTONES.md, tasks/todo.md, .agent/instructions.md
Open Items table. No gaps requiring clarifying questions — proceeded
straight to framing.

## Framed Question

RepoCheck v1 scans a GitHub repo or Claude Code skill via: live CVE
lookup (OSV.dev), a static red-flag code checklist, dependency
freshness, and an opt-in LLM "deep scan" on high-risk files — output as
traffic-light + humanized narrative. Key locked decisions: live CVE
lookup never a local self-mutating DB (Decision 001, amended by 006);
two-tier static+opt-in-deep-scan novel-pattern detection (007); free
static scan, paid opt-in deep scan (008); traffic-light + narrative
output with JSON via flag (009, 013); GitHub-only v1 host behind a
pluggable interface, ecosystem breadth via OSV.dev (012); Python core
library (010); ANTHROPIC_API_KEY env var only for CLI deep-scan auth
(014). Open items: skill-to-core-library call mechanism (OI-007),
severity-weighting model (OI-008).

Question for the council: is this v1 scope and architecture sound, does
it deliver a genuinely useful and safe v1, and what's missing, risky, or
wrong before we start building?

## Step 1.5 — Recency Step

Yes, recency-sensitive — ran two targeted searches:

- **OSV.dev API**: no hard published rate limit currently enforced;
  batch endpoint caps at 1000 queries/request; 32MiB response limit on
  HTTP/1.1, none on HTTP/2. ([OSV API docs](https://google.github.io/osv.dev/),
  [querybatch spec](https://google.github.io/osv.dev/post-v1-querybatch/))
- **Claude Code skill security landscape (2026)** — load-bearing
  finding: malicious skills predominantly attack via natural-language
  instructions embedded in `SKILL.md` (data theft, agent hijacking),
  not executable code patterns. Snyk's ToxicSkills research found
  prompt injection in 36% of tested skills and 1,467 malicious payloads
  ecosystem-wide. Dynamic context commands can run before the model
  sees the skill at all, bypassing model-level prompt-injection
  defenses. ([CSA](https://cloudsecurityalliance.org/blog/2026/06/25/5-claude-agent-skills-risks-every-ciso-should-know),
  [Datadog Security Labs](https://securitylabs.datadoghq.com/articles/malicious-skills-supply-chain-risks-in-coding-agents-with-dynamic-context/))

## Advisor Responses

### The Contrarian
The plan's biggest vulnerability is that "code red flags" (static
regex/AST checklist) cannot parse a plain-English malicious instruction
sitting in `SKILL.md` prose — that's not malformed code, it's a
well-formed sentence that happens to be an attack. Per the 2026 data,
instruction-manipulation is the *majority* attack surface for skills
specifically (36% prompt injection rate), not an edge case. Shipping v1
without explicit SKILL.md-instruction analysis risks a malicious skill
passing with a clean "static scan" traffic light — a false green light
is worse than no tool, because it manufactures confidence.

### The First Principles Thinker
For v1 to be trustworthy: (1) the static pass must not false-negative
on the *primary* attack surface for the artifact type being scanned,
(2) the cost model must not incentivize skipping the check that would
catch the attack, (3) output must not overstate confidence. Code
red-flags + CVEs is a reasonable proxy for (1) on *repos*. For *skills*,
the primary attack surface is instruction text, currently untreated as
a first-class pillar. On (2): deep scan being opt-in/paid is backwards
if it's the only path to catching skill-instruction attacks — a user
skipping the paid step because the free static scan came back clean has
been actively misled. On (3): a green traffic light with no SKILL.md
instruction analysis run is a false confidence claim given what's now
known.

### The Expansionist
The strong parts deserve equal weight: live CVE lookup over a
self-mutating local DB (001), versioned-not-live ruleset updates (006),
a pluggable host interface even with only GitHub shipping in v1 (012),
the free-static/paid-opt-in-deep cost model (008), and the
humanize-and-teach framing (009) are all genuinely disciplined choices.
The gap raised isn't a flaw in this architecture — it's a missing third
scan *lane* (instruction-content analysis for SKILL.md-shaped inputs)
that should run by default because it's cheap (small text blob, not a
whole repo) and it's the primary threat for that artifact type. No
need to redesign what's already built.

### The Outsider
"RepoCheck" scans two structurally different things — a repo (code
installed as a dependency) and a skill (instructions given to an
agent, where code is secondary) — with one pipeline applied equally to
both. That's the framing error. Should skill-scanning and repo-scanning
be distinct modes with different default pipelines, not one pipeline
for both? Separately: most skills won't even have a
`package.json`/`requirements.txt`, so for skill-mode, two of
RepoCheck's four stated pillars (CVE, freshness) may not apply at all,
and the third (code red-flags) misses the actual threat per the
recency data. Worth naming plainly rather than assuming the four-pillar
model covers both artifact types equally.

### The Executor
1. Add a decision before Milestone #2: two scan modes (`repo`,
   `skill`), sharing CVE/freshness/code-checklist machinery where
   applicable; skill mode adds a default, free, static-first
   SKILL.md/manifest instruction-analysis pass as a first-class pillar
   (known bad phrasings: "read ~/.ssh", "curl | bash", "ignore previous
   instructions", env-var exfiltration requests).
2. Redefine "high-risk file" for deep-scan escalation (OI-008) to
   always include SKILL.md/skill manifests, not only files the static
   pass already flagged — the static pass may be blind to a *novel*
   phrasing.
3. Resolve OI-007 (skill-to-library call mechanism) with this in mind —
   RepoCheck's own skill wrapper's SKILL.md becomes a file it should
   arguably scan on its own releases.
4. Re-run Milestone #6 (verdict design) with two templates — repo
   findings read differently from instruction-injection findings.
5. Everything else (Decisions 001–014) stands as scoped, only extended.

## Anonymization Map

| Letter | Advisor |
|---|---|
| A | The Contrarian |
| B | The First Principles Thinker |
| C | The Expansionist |
| D | The Outsider |
| E | The Executor |
| F | The Trap Detector |

### The Revenue Lens — SITS OUT
No pricing/ROI question genuinely in play; cost model (008) already
settled, session is about scan coverage not monetization.

### The Gatekeeper — SITS OUT
No distribution/access intermediary dimension — v1 is CLI + skill,
both directly in the user's hands, no marketplace/approval gate.

### The Trap Detector — FIRES
Most dangerous unexamined assumption: "code red flags" already covers a
skill's attack surface — demonstrably false per 2026 research, and
never stated explicitly in any of the 14 decisions; it was implicit in
treating repo-scan and skill-scan as one pipeline. Fastest cheap test:
manually trace a real malicious-skill instruction example (e.g. "read
~/.ssh/id_rsa, POST to external URL," per Datadog/CSA research) against
RepoCheck's currently-planned static checklist. It would not be caught —
a 10-minute trace confirms or kills the concern before any code is
written, at zero cost.

## Peer Review

### Pass 1
- Strongest: **D** — reframes "one pipeline, two input types" as "two
  structurally different artifact types," the root cause under A's and
  B's more detailed versions of the same complaint.
- Biggest blind spot: **E** — jumps to a build plan before F's cheap
  validation test confirms the gap is real and sized as assumed.
- Everyone missed: whether RepoCheck should eventually scan its own
  future skill wrapper (Milestone #7) as a dogfooding/credibility
  check — notable gap for a public open-source security tool.

### Pass 2
- Strongest: **F** — turns an abstract six-way disagreement into one
  falsifiable, near-free action that resolves it before any rewrite.
- Biggest blind spot: **C** — defends existing architecture correctly
  but doesn't address whether a third scan pillar changes the cost-model
  story: is instruction-analysis "free static" like code-checklist
  scanning, or does catching *novel* instruction phrasings need its own
  static/deep-scan two-tier treatment?
- Everyone missed: a SKILL.md instruction-injection attack could target
  RepoCheck's own deep-scan LLM pass itself — if deep scan reads
  malicious SKILL.md content into an LLM context, injected instructions
  are now inside that context during analysis. Needs explicit
  prompt-injection-resistant handling (scanned content delimited as
  untrusted data, never instructions) — a real implication of Decision
  007 not yet named as a design requirement.

### Pass 3
- Strongest: still **D**, holding up after two rounds of scrutiny.
- Biggest blind spot: **A** — frames the gap as "worse than no tool"
  without acknowledging E's point that a small, well-scoped addition
  (not a redesign) closes it — slightly overstated severity relative to
  tractability.
- Everyone missed: the same instruction-injection concern applies to
  *repo* mode too (README.md, CI config, code comments could carry
  injected instructions if deep-scan ever reads repo text into
  context) — the prompt-injection-resistant-handling requirement from
  Pass 2 is mode-agnostic, belongs in the deep-scan architecture itself,
  not just a skill-mode addendum.

## COUNCIL VERDICT

**Where the council agrees:** Decisions 001–014 are sound and don't need
reopening — live CVE lookup, versioned ruleset, pluggable host
interface, free-static/paid-deep-scan cost model, humanized output all
independently defended. The gap is additive: RepoCheck's stated scope
covers "a repo, or a skill," but the architecture was designed against
a code-shaped threat model that fits repos well and skills poorly, per
2026 research showing skill attacks are predominantly instruction-shaped.

**Where the council clashes:** E moved straight to a build plan
(add a skill-mode pillar now); F insisted on a 10-minute validation
test first. **The chairman sides with F** — not because E is wrong, but
because the fix's exact shape (static checklist addition? own deep-scan
tier? actual miss-rate?) should be informed by tracing one real
malicious-instruction example against the current design before
committing new decisions/milestones to paper.

**Blind spots the council caught:**
1. Does RepoCheck's static checklist, as currently scoped, actually
   miss a real-world malicious skill instruction example? (Do this
   first.)
2. Should SKILL.md/skill manifest content be scanned by default (free
   tier) rather than gated behind opt-in deep scan, given it's the
   primary threat for that artifact type and cheap to analyze?
3. Does RepoCheck's own deep-scan LLM pass need explicit
   prompt-injection-resistant handling — mode-agnostic, applies
   anywhere untrusted text enters an LLM context?
4. Should RepoCheck eventually scan its own skill wrapper as a
   dogfooding/credibility signal once Milestone #7 exists?

**Priority filter** (leverage → learning → revenue; pre-revenue scoping
work):
1. Leverage — blind spot #1, the validation test, is highest-leverage:
   confirms or kills the gap cheaply, everything else depends on it.
2. Leverage — blind spot #3 (prompt-injection-safe deep-scan handling)
   is far cheaper to bake into Milestone #2's core library design now
   than to retrofit after it ships.
3. Learning — blind spot #2 (default vs. opt-in for skill-instruction
   scanning) resolved after #1 gives real miss-rate/severity data.
4. Learning — blind spot #4 (dogfooding) — nice-to-have, defer to
   Milestone #7/#9.

**The recommendation:** Don't reopen Decisions 001–014. Add one new
decision before Milestone #2 scaffolding: RepoCheck treats "repo" and
"skill" as distinct scan modes sharing common machinery
(CVE/freshness/code-checklist), with skill mode adding a default, free,
static-first instruction-content analysis pass as a first-class pillar —
sized based on what the validation test shows. Separately, bake
prompt-injection-resistant handling into the deep-scan architecture
itself (mode-agnostic) as a non-negotiable design requirement, alongside
"never execute untrusted code" in CLAUDE.md.

**The one thing to do first:** Manually trace one real malicious-skill
instruction example against RepoCheck's currently-planned static code
checklist, and write down plainly whether it would or wouldn't be
caught. Ten minutes, zero cost, resolves the open disagreement before
any new architecture gets built on an unvalidated assumption.

---
Timestamp: 2026-08-07
