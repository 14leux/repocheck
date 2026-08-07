# KNOWLEDGE.md

Confirmed learnings only — bugs and root causes, infra/library quirks,
anything that took real effort to figure out.

## Session 1 — manual validation trace against a real repo

Traced `https://github.com/browser-use/browser-use` (108k stars, real
production repo with real skills) by hand through the currently-planned
detection logic, per the council's repeated recommendation to validate
before building further.

**OSV.dev batch lookup works as designed.** POSTing 6 pinned dependency
versions from `pyproject.toml` to `https://api.osv.dev/v1/querybatch`
returned real results: `pillow==12.2.0` had 26 real advisory IDs (GHSA +
PYSEC), while `aiohttp`, `requests`, `cloudpickle`, `python-dotenv`, and
`pydantic` at their pinned versions came back clean. First real
end-to-end proof the CVE pillar (Decision 011) works as specified, with
both a true positive and true negatives in one sample.

**Manifest-only install-hook check produced a correct true negative.**
No `postinstall`/build-hook scripts found in `pyproject.toml` — the
"install-time script" red flag correctly found nothing to flag here.

**Real skills fetch-and-follow external URLs at runtime — a risk
category the plan hadn't named.** `skills/browser-use/SKILL.md` (a
large, legitimate, popular skill) routinely instructs the agent to read
external URLs at runtime for setup/mechanics detail (e.g. "for
connection problems, read
https://github.com/browser-use/browser-harness/blob/main/install.md").
This is normal progressive-disclosure design, but it is structurally
identical to the primary attack vector the 2026 research described
(Decision 015's context): content fetched dynamically at use-time is
not the content RepoCheck would have scanned at review-time — a
time-of-check/time-of-use gap a static one-time content scan cannot
close. This can only be surfaced as an honestly-caveated risk factor
("this skill dynamically fetches and follows external content, which
RepoCheck cannot verify at scan time"), never resolved to a clean
pass/fail. See DECISIONS.md #020.

**Found a real false-positive candidate for the deferred allowlist
question.** The same `SKILL.md` contains `printf '%s'
"$BROWSER_USE_API_KEY" | browser-use auth login --api-key-stdin` —
piping a secret via stdin, the *secure* way to avoid leaking a key into
shell history or the process list. A naive "env var + pipe" pattern
rule would flag this as suspicious when it is actually best practice.
Concrete test case for the deferred false-positive/allowlist open item
(see `.agent/instructions.md` Open Items).

**GitHub's hosted code-search API (`gh api search/code`) gave
unreliable results for a quick eval/exec/subprocess sweep** — likely
indexing lag and/or query-syntax quirks, not a true negative on the
repo. RepoCheck's code red-flag pillar should fetch raw file content
through its own file-access interface (Decision 012) and run pattern
matching locally, never rely on a host's hosted search API as the
detection mechanism.

**`gh` CLI is available and authenticated on this machine** and is a
fast, reliable way to prototype GitHub API calls (`gh api
repos/OWNER/REPO/contents/PATH --jq '.content' | base64 -d`) before any
core library code exists — useful for further manual validation passes.

## Session discipline

**`tasks/wip.md` was never updated during session 1 — only written empty
at boot and left empty.** It read as "clean" at close by accident, not
by discipline. Had this session crashed at any point, the crash pad
would have protected nothing, and the next session would have had to
re-derive several hours of scoping from the git history alone.
`PROJECT_DISCIPLINE.md` §5 is explicit that wip.md only works if kept
live *during* the session, updated at every pivot — a crash pad that is
only accurate at the moment of a clean close is useless for its actual
purpose. Session 2 must update wip.md at each milestone step, starting
at boot.
