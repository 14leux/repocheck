# RepoCheck

Check whether a GitHub repo or a Claude Code skill is safe to trust —
before you install it, not after.

RepoCheck looks up known vulnerabilities in a repo's dependencies,
scans its code (or, for a skill, its instructions) for red-flag
patterns, checks how stale its dependencies are, and gives you a
plain-language verdict: **CLEAR**, **CAUTION**, or **DANGER** — with
every finding explained in terms a non-expert can act on, not just a
CVE ID to go look up yourself.

## Install

Nothing to install. RepoCheck is pure Python standard library — no
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
