# Dr. RepoCheck

*A check-up for code you're about to trust — before you install it, not after.*

## The five-second decision that's actually a big deal

You found a repo on GitHub, or a skill someone shared, that does exactly
what you need. It has stars, it looks legit, someone in a Discord
vouched for it. You `git clone` it, or you drop it into Claude Code, and
you move on. That whole decision took about five seconds.

This is completely normal, and it's also how most real damage gets in.
Not through some genius hack — through *trust granted on autopilot*.
Psychologists have a name for the shortcut your brain just took:
**social proof** (stars and a polished README read as "other people
already checked this, so I don't have to") and **optimism bias** ("this
kind of thing happens to other people, not to my project"). Neither
feeling is a security check. It just feels like one, which is what
makes it risky — the feeling of safety and actual safety are two
different things, and only one of them stops an attacker.

This gap matters more now than it used to. "Vibe coding" — describing
what you want and letting an AI agent write, fetch, and run code for
you — means you're often trusting a repo or a skill *faster and more
often* than you would if you were reading every line yourself. The
agent doesn't get a gut feeling of unease reading a suspicious
`postinstall` script the way a human skimming it might. It just runs
it, if you let it. That's not a flaw in AI agents — it's exactly why a
second pair of eyes, even an automated one, is worth having *before*
the clone or the install, not as a post-mortem after something goes
wrong.

Dr. RepoCheck is that second pair of eyes. Point it at a GitHub repo or
a Claude Code skill, and it looks up known vulnerabilities in its
dependencies, scans its code (or, for a skill, its *instructions* — see
why that's different below) for red-flag patterns, checks how stale its
dependencies are, and gives you a plain verdict: **CLEAR**, **CAUTION**,
or **DANGER** — with every finding explained in terms you can act on,
not a CVE ID you're left to go look up yourself. It doesn't replace
your judgment. It just makes sure your judgment is working from actual
evidence instead of a vibe.

*(A naming note: the project is Dr. RepoCheck, but the command, the
Python module names, and the GitHub repo itself are still `repocheck` —
changing those would break every existing clone and install command, so
only the name you *see* changed, not the one you *type*.)*

## Install

Nothing to install. Dr. RepoCheck is pure Python standard library — no
`pip install` required.

- **Python 3.11 or newer** (uses `tomllib`, added in 3.11).
- Optionally, a `GITHUB_TOKEN` environment variable (a
  [personal access token](https://github.com/settings/tokens), no
  scopes needed for public repos) to avoid GitHub's low unauthenticated
  rate limit. Not required for occasional use.

Clone the repo and run it directly:

```bash
git clone https://github.com/14leux/repocheck.git
cd repocheck
python repocheck.py pallets/itsdangerous
```

## Usage

```bash
# Scan a repo
python repocheck.py owner/repo
python repocheck.py https://github.com/owner/repo

# Scan a skill (auto-detected from a pasted GitHub file URL, or pass the path explicitly)
python repocheck.py https://github.com/owner/repo/blob/main/skills/x/SKILL.md
python repocheck.py owner/repo path/to/SKILL.md

# Machine-readable output for scripts/CI
python repocheck.py owner/repo --json
```

Exit code reflects whether the scan *completed reliably* — 0 for a
finished scan (regardless of verdict color), 1 for a failed or
degraded one (a source was down, the repo didn't exist, etc.). Check
the verdict field/color for the actual security result.

### What gets checked

**Repo mode** — four pillars, combined into one verdict:
1. **Known CVEs** in declared dependencies, looked up live against
   [OSV.dev](https://osv.dev) at scan time (never a local, self-updating
   database — see `DECISIONS.md` #001 for why).
2. **Code red flags** — obfuscated payloads, credential-harvesting
   patterns, suspicious network calls, install-time scripts.
3. **Dependency freshness** — how far behind (or genuinely abandoned)
   each dependency is, distinguishing pinning *style* from real
   staleness.
4. A **plain-language verdict** combining all three, with the most
   severe finding always driving the color (never averaged away).

**Skill mode** — the differentiated case. The dominant real-world
attack on Claude Code skills is instructions embedded in `SKILL.md`
prose, not obfuscated code, so skill mode runs a dedicated,
default (free) instruction-content scan for credential-exfiltration
phrasing, prompt-injection/override attempts, and download-then-execute
patterns — plus an honest caveat, not a false pass, when a skill
dynamically fetches and follows external content that RepoCheck can't
verify at scan time.

### Deep scan (optional, costs money, off by default)

Static pattern matching has a real precision ceiling — a sufficiently
different phrasing or unfamiliar library can slip past it (see
`KNOWLEDGE.md` for concrete examples this project found in its own
testing). For a closer look, an opt-in deep scan sends the highest-risk
files to an LLM for reasoning-based review:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python deep_scan.py repo owner/repo --confirm
python deep_scan.py skill owner/repo path/to/SKILL.md --confirm
```

Omit `--confirm` to see which files would be sent and what it would
cost, without spending anything. Inside a Claude Code session, the
`repocheck` skill does this reasoning directly using the session itself
— no separate API key needed (see `skills/repocheck/SKILL.md`).

**Why you're asked for your own key, not RepoCheck's:** Dr. RepoCheck
doesn't run its own AI service, bill you through a middleman, or see
your key pass through anyone else's server — the standalone
`deep_scan.py` command talks directly from your machine to Anthropic's
API using a key only you hold. That's a deliberate tradeoff: it means
this tool can never rack up a bill on your behalf, silently proxy your
key somewhere, or become a place your key is stored — because it never
touches it except to pass it straight through to Anthropic, once, for
the call you explicitly confirmed.

### Protecting your API key

An API key is a password that spends money and acts with your account's
permissions — anyone who has it can use it as *you*, on your bill,
until you notice and revoke it. Treat it the way you'd treat a spare
house key, not a screen name: fine to use, not fine to leave lying
around or hand to someone because they asked nicely.

**Do:**
- Set it as an environment variable (`export ANTHROPIC_API_KEY=sk-ant-...`),
  never typed into a script or committed to a file.
- Give it an **expiration** when you create it — the
  [Anthropic Console](https://console.anthropic.com/settings/keys) lets
  you pick 3 hours, 1 day, 7 days, 30 days, a custom window, or never.
  For a one-off deep scan, a short expiry (a day or a week) means that
  even if the key leaked somehow, it stops working on its own — you
  don't have to catch and revoke it in time.
- Scope it to its own **workspace** in the console if you have one, so
  it can only run up charges in that workspace, not your whole account.
- Rotate it periodically (Anthropic's own guidance: quarterly at
  minimum) and immediately if you have any reason to suspect it leaked.
- Keep an eye on usage/billing in the console — a spike you didn't
  cause is the first sign a key got out.

**Don't:**
- Don't paste it into chat, a Discord/Slack message, a GitHub issue, a
  support ticket, or a screenshot — all of those get logged, cached, or
  indexed somewhere outside your control, even in a "private" channel.
- Don't commit it to a repo, even a private one — private repos get
  forked, cloned, backed up, and occasionally made public by accident,
  and the key is still readable in the git history afterward even if
  you delete it in a later commit.
- Don't hardcode it directly in source code where a `git blame` or a
  stray `print()` could expose it.
- Don't share one key across unrelated projects — if one leaks, you'd
  rather revoke a key that only ever touched that one thing.

If a key ever does leak, revoke it immediately in the console and issue
a new one — that takes less time than dealing with the aftermath.

(Sources: [Anthropic's own key-management guidance](https://platform.claude.com/docs/en/manage-claude/authentication),
[OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).)

### Suppressing a known-good finding

If RepoCheck flags something in your repo that you've reviewed and
judged safe, add a `.repocheck-allow.json` file to the repo's root:

```json
[
  {
    "category": "shell-pipe-execute",
    "path": "scripts/install.sh",
    "reason": "reviewed 2026-08-07, this is our own trusted installer, not third-party content"
  }
]
```

Suppressed findings are still shown in the output, with the reason
attached — never silently hidden.

## Glossary

For readers who aren't security specialists:

- **CVE** — a publicly cataloged, known security flaw in a specific
  piece of software. If a CVE exists for the exact version you're
  running, an attacker can look up the same public record.
- **CVSS** — the standard 0–10 severity score attached to most CVEs;
  RepoCheck buckets this into critical/high/moderate/low.
- **OSV.dev** — the open, free vulnerability database RepoCheck queries
  live for CVE data, covering most language ecosystems in one place.
- **Static scan** — pattern-matching over code/text without running
  anything or calling an LLM. Free, fast, the default.
- **Deep scan** — an opt-in pass where an LLM reads flagged content and
  reasons about it, catching things a fixed pattern list can't. Costs
  money, never runs without explicit confirmation.
- **Red flag** — a specific pattern RepoCheck's static scan looks for
  (e.g. code that reads an SSH key and sends it over the network).
- **Traffic-light verdict** — CLEAR / CAUTION / DANGER, driven by the
  single most severe finding, never diluted by averaging with clean
  results.
- **Degraded scan** — one where a data source (GitHub, OSV.dev) failed
  partway through; the verdict says so explicitly rather than silently
  looking like a clean result.
- **API key** — a private credential that lets a service act as you and
  bill your account; see "Protecting your API key" above before you
  create one.

## Contributing

See `CONTRIBUTING.md` — in particular, how to propose a new red-flag
pattern (the detection rules are a versioned, human-reviewed ruleset,
never a live self-updating feed — see `DECISIONS.md` #006).

## Project history and design decisions

This project runs on a lightweight version of a personal project-
discipline framework — every architectural decision, rejected
alternative, and tradeoff is logged as it's made, not reconstructed
after the fact:

- `DECISIONS.md` — the full decision log (23 entries as of M12),
  including why RepoCheck never builds a local vulnerability database,
  why the CLI and skill share one core library, and how the severity
  model works.
- `KNOWLEDGE.md` — confirmed learnings, including real bugs found by
  testing against real repos (an npm version-range bug, several
  detection evasions, a false-positive flood from a test fixture) and
  how they were fixed.
- `MILESTONES.md` — the build plan and what's actually done vs. still
  open, with acceptance criteria tied to real, reproducible test
  results rather than assumptions.

### Origin

Born out of a real need in a different project (`oracle_aura`): on
2026-08-04, a GitHub repo (PixelRAG) was manually scoped and
security-reviewed before being trusted, checked against known threats
by hand. That was a one-off, manual pass. RepoCheck turns that into a
reusable tool anyone can point at a repo or skill before installing it.

## License

MIT — see `LICENSE`.
