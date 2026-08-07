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

## Session 2 — M2 walking skeleton

**`skeleton.py` (stdlib-only Python, no dependencies to install) passed
all three M2 acceptance criteria on the first working version.**
Reproduced the M1 manual trace against `browser-use/browser-use` exactly
(`pillow==12.2.0` → the same 26 advisories) and, because it checks all
36 dependencies instead of the 6 manually sampled in M1, found two real
vulnerabilities the manual pass never looked at: `click==8.3.1` and
`mcp==1.26.0`. This is the point of automating it — full coverage beats
a spot check even when the spot check was correct as far as it went.

**Ecosystem-agnostic by construction, not by extra code.** Running the
identical script against `expressjs/express` (npm) required zero code
changes and correctly found a real advisory
(`body-parser==2.2.1` → GHSA-v422-hmwv-36x6). DECISION 011's bet on
OSV.dev as a single multi-ecosystem source is paying off exactly as
designed — ecosystem breadth came for free.

**`google/osv.dev` itself is a genuinely good multi-ecosystem monorepo
test case** — 19 manifest files (Go, PyPI, npm) spread across
subdirectories, 632 dependencies total, recursive tree walk found all of
them with no truncation. Also flagged a real `cryptography` CVE in
OSV.dev's own Docker build and a `golang.org/x/crypto` advisory repeated
across five of its own go.mod files — a nice confirmation that the tool
works, tested against the tool whose data it depends on.

**GitHub's recursive tree API (`git/trees/{branch}?recursive=1`)
returns a `truncated` field for oversized repos** — added an explicit
warning path in `skeleton.py` rather than silently under-scanning. Not
yet triggered by any repo tested; still untested against something that
actually trips it (relevant to the still-open "very large repo" question
from earlier scoping).

**Windows console defaults to cp1252**, so the em-dash in the vulnerable-
dependency output mangled on first run. Fixed with
`sys.stdout.reconfigure(encoding="utf-8", errors="replace")` — this is
the same lesson already recorded in the user's global CLAUDE.md; worth
confirming any future script in this project does the same.

**GitHub's authenticated rate limit (`gh auth token` piped into
`GITHUB_TOKEN`) was more than sufficient** for these three scans —
`google/osv.dev` alone needed 20 API calls (1 tree listing + 19 file
fetches) and hit no limit.

## Session 2 — M3 skill-mode instruction scan

**`skill_scan.py` passed both true-negative and true-positive tests —
the first real proof this detection category works at all, not just
that it stays quiet on safe content.** Against the real
`browser-use/browser-use` skill: zero false positives (the
`api-key-stdin` allowlist worked exactly as designed) and the
dynamic-external-content caveat fired correctly, naming `github.com`.
Against three synthetic examples built from the exact patterns in the
2026 research and DECISIONS.md #015/#020 (credential read + POST
exfiltration, instruction-override phrasing, `curl | bash`), all three
were caught. This closes the loop the Contrarian advisor opened in
session 1: "never tested against a single real example."

**The allowlist-vs-red-flag distinction needed a full-line check, not a
bare pattern match, to work at all** — `skill_scan.py` extracts the
whole line around each pipe match and runs the safe-stdin allowlist
against that full line, not just the regex match's own span, specifically
because the safe subcommand (`| tool auth login --api-key-stdin`) sits
later on the line than the pipe character itself. Designed this way from
the start based on the real OI-013 example, not discovered as a bug
during testing — worth noting the distinction honestly rather than
implying a debug story that didn't happen.

**Credential-exfiltration detection is a co-occurrence check, not a
proximity check, and that's a known limitation, not an oversight.** It
flags a sensitive-path pattern and a network-send pattern appearing
anywhere in the same document, not specifically near each other. This
was a deliberate choice for M3 (documented in skill_scan.py's docstring)
— proximity-aware matching is more precise but meaningfully more complex
to write correctly, and a same-document co-occurrence is still a
legitimate finding worth a human's attention even if a later version
narrows it.

## Session 2 — M4 repo-mode code red-flag scan

**`code_scan.py` passed all three acceptance criteria plus true-positive
validation across all four detection categories.** True negative
confirmed on a real repo (`pallets/itsdangerous`, 17 files, zero false
positives) and on the specific M1-recorded case (`browser-use`'s
`pyproject.toml`, confirmed no install hooks via direct file check, not
a full-repo scan). True positives confirmed via synthetic examples for
obfuscation (`exec(base64.b64decode(...))`), credential-harvesting
(reading `~/.ssh/id_rsa` + `requests.post` in the same file), suspicious
network calls (raw-IP URL), and install-time scripts (`package.json`
`postinstall`).

**Streaming-for-memory and scaling-for-API-calls are two different
problems, and only the first is solved.** `code_scan.py` fetches, scans,
and discards one file's content at a time, so memory use doesn't grow
with repo size — that's what M4's acceptance criterion asked for.
But each file still costs one GitHub contents-API call, so a repo with
thousands of matching files is slow and API-call-expensive regardless of
memory use. Capped at 300 files with an explicit note rather than
silently truncating. Recorded as OI-017, distinct from OI-015 (which is
about not depending on GitHub's *search* API) — this is about the
*contents* API's per-file cost, a real scaling question for M9's opt-in
deep scan too, since it will fetch some of the same files.

## Session 2 — M5 dependency freshness signal

**Real bug caught by testing, not by review.** First version of
`classify()` checked `pinned_version == latest_version` before checking
staleness, so `nose==1.3.7` — genuinely abandoned, last released ~11
years ago (4084 days) — read as "current" simply because no newer
version was ever published. Fixed by checking abandonment first,
independent of whether the pin happens to equal "latest": a package
whose only release was over a decade ago is "latest" by definition and
still abandoned, and being pinned to that latest version does not make
it current. This is the same shape of lesson as M3's allowlist work —
the first version that looks right on the case it was written for still
needs a real edge case run through it.

**After the fix, `browser-use/browser-use` correctly showed 3 of 36
dependencies as "pinned and abandoned"** (`InquirerPy`, `screeninfo`,
`uuid7` — all genuinely 4+ years since their last PyPI release). This
initially looked like it violated M5's acceptance criterion ("browser-use
pins everything exactly, which must not read as stale") until re-reading
the criterion's actual intent: exact-pinning *style* must not be
conflated with staleness, which is what's being tested (and correctly
holds — the other 33 dependencies are not falsely flagged). It does not
mean browser-use's real dependencies can never be genuinely stale. Worth
recording precisely because it's the kind of ambiguity that could be
misread as a regression by a future session skimming the milestone
table without the detail.

## Session 2 -- M6 severity model + humanized verdict

**Two real bugs found by actually running the full pipeline against a
large, real repo -- neither would have surfaced from unit-level
synthetic tests alone.**

**Bug 1: `suspicious-network-call` flooded the verdict with 75+ false
positives**, almost entirely from `browser-use`'s own
`tests/ci/security/test_ip_blocking.py` -- a file that exists
specifically to test their IP-blocking logic and is therefore packed
with example IP addresses (`127.0.0.1`, `192.168.x.x`, `10.x.x.x`,
well-known public DNS resolvers). The raw-IP pattern from M4 had no
concept of "this address can never be a real exfiltration destination."
Fixed at the rule level, not by suppressing test files wholesale
(malicious code can hide in a `tests/` directory too): private,
loopback, reserved, and link-local IPs are structurally incapable of
being an external attacker's collection endpoint, so they're excluded
outright via Python's `ipaddress` module. Remaining public IPs
(`8.8.8.8` etc.) found in test-file-shaped paths get a distinct,
lower-severity category rather than being dropped -- still visible,
correctly weighted. This cut total findings on `browser-use` from 107
to 58 findings, entirely by removing noise, with zero change to the
real signal (33 CVE findings untouched).

**Bug 2: `--json` output was corrupted by the pre-flight message
printing to stdout before the JSON.** `python verdict.py ... --json`
produced invalid JSON because "Pre-flight: scanning..." landed on the
same stream as the JSON payload. Fixed by routing all progress/pre-flight
text to stderr, keeping stdout reserved exclusively for the actual
verdict output (text or JSON) -- this is the same shape of gotcha that
would break any downstream tool piping RepoCheck's `--json` output.

**Running the full pipeline against a large real repo (`browser-use`,
390 candidate source files) took ~6 minutes**, entirely from sequential,
uncached network calls stacking across all three pillars (CVE batch +
~10 severity detail fetches + up to 300 code-scan file fetches + 36
freshness lookups, one HTTP round-trip at a time, no concurrency).
Recorded as OI-019 -- concurrency/caching is real, necessary future
work, distinct from OI-017's per-file API-call-count concern (this is
about wall-clock time, not call count). The pre-flight estimate was
fixed to compute from actual scope (manifest + candidate-file counts)
rather than a static "seconds to low minutes" claim that was simply
wrong for this repo -- came within ~25% of actual wall-clock time on the
one real test.

**Final verdict on `browser-use/browser-use`: CAUTION**, driven by real
HIGH-severity CVEs (`mcp`, `pillow`) with the corrected low-severity
test-context noise clearly separated out -- the kind of result a
security-literate reader would actually agree with, which was the
literal wording of M6's last acceptance criterion.

## Session 2 -- M7 extract the pluggable interfaces

**The chokepoint DECISION 021 bet on already existed, cheaply, because
every script imported `list_tree`/`fetch_file` from `skeleton.py`
rather than calling GitHub's API directly.** That meant extracting
`FileAccessProvider` required touching exactly two files
(`skeleton.py` to delegate through a swappable module-level provider,
plus the new `github_provider.py` holding the moved-verbatim GitHub
implementation) and zero changes to `skill_scan.py`, `code_scan.py`,
`freshness_scan.py`, or `verdict.py` -- confirming the sequencing bet
in DECISION 021 was right: the interface shape fell out of how the
working code was already organized, rather than needing to be guessed
in advance.

**The swap was proven with a real fake provider, not asserted.**
`test_provider_swap.py` serves canned in-memory data with zero network
calls, swaps it in via `skeleton.swap_provider()`, and runs
`find_manifests`/parser (`skeleton.py`) and `scan_file_content`
(`code_scan.py`) against it unmodified. Both passed. This is the literal
M7 acceptance criterion ("demonstrated by a stub, not asserted") --
worth noting because it would have been easy to just claim the
interface was swappable by design without actually building a second
implementation to prove it.

**`ModelProvider` (for M9's deep scan) is forward-defined, not
extracted, and that's an honest limitation, not an oversight.** There's
no working deep-scan code yet to extract an interface from -- M9 hasn't
been built. Defined the interface shape now (with the DECISIONS.md #016
untrusted-content requirement noted directly in its docstring) so M9
can be written against it directly, but its "swap and prove nothing
breaks" claim can't be demonstrated the same way until M9 exists to
call it.

**Full M2-M6 re-verification after the refactor reproduced every result
exactly** -- same CVE list on `browser-use`, same skill-scan caveat, same
freshness abandoned-count (3), same clean code-scan on
`pallets/itsdangerous`. Zero regressions from the refactor.

## Session 2 -- M8 CLI wrapper (V1 complete)

**`repocheck.py` auto-detects mode from three real usage patterns, not
just a flag.** A bare `owner/repo` defaults to repo mode; a second
positional argument (a path) switches to skill mode; and -- the nicest
one -- pasting a full GitHub blob URL to a `SKILL.md` file (exactly
what copying a link from GitHub's UI gives you) is parsed directly into
owner/repo/path and defaults to skill mode, with zero extra flags
needed. All three tested against real targets and produced identical
results to the equivalent explicit invocation.

**V1 is complete: M1 through M8, all DONE, all acceptance criteria met
or honestly recorded as partially met with a tracked follow-up
(M3/OI-016's real-malicious-sample gap).** Every pillar was validated
against real repos, not just synthetic tests, and two genuine bugs (the
IP false-positive flood in M6, the abandoned-package misclassification
in M5) were caught by that validation and fixed before being called
done -- not found later by a user. `repocheck.py owner/repo` today
does what the project's origin story (a manual PixelRAG review) took a
human doing it by hand to do.

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
