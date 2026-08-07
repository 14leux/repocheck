# RepoCheck

A tool/skill that checks whether a GitHub repo (or a Claude Code skill you're
about to install) is safe to run — audited against current-year security
standards and known threats — rather than trusting it on sight.

## Origin

Born out of a real need in `oracle_aura`: on 2026-08-04 we manually scoped
and security-reviewed a GitHub repo (PixelRAG) before trusting it, checking
it against 2026 security standards and known threats. That was a one-off,
manual pass. RepoCheck is the idea of turning that into a reusable tool
other people can point at any repo or skill before they install it.

## What it's for

- Input: a GitHub repo URL, or a Claude Code skill someone is about to add.
- Output: a security assessment — known CVEs in its dependencies, red flags
  in the code itself (obfuscation, suspicious network calls, credential
  harvesting patterns), how current its dependencies are, and a plain-
  language verdict.
- End state: usable by Mailu personally first, then a public GitHub repo
  so other people can run it (or contribute to it) themselves.

## Key design decision (already made, don't relitigate)

**Live lookup at scan time, not a self-mutating local threat database.**
The original framing was "a repo that checks and updates itself on the
newest threats." That's the wrong shape — a tool that mutates its own
knowledge base needs a maintained feed and a scheduled job behind it, and
staleness creeps in the moment that job breaks silently (a failure class
`oracle_aura` has hit more than once — see its `tasks/lessons.md` Lessons
81/82/87 for what that looks like: something reports success while quietly
doing nothing).

Instead: query live sources (CVE databases, GitHub Security Advisories,
npm/PyPI/PyPA advisory feeds, OSV.dev) at the moment of each scan. No local
database to go stale. This is the same pattern the existing `security-review`
Claude Code skill already uses — RepoCheck can likely start as a variant or
extension of that pattern rather than inventing a new one.

## Naming

Landed on **RepoCheck** over SkillCheck (too narrow — implied skills only,
not repos) and a few generalized alternatives (SourceCheck, Vetly, Auditly,
Clearance) considered along the way. Open to revisiting once the product
shape is clearer.

## Status

Scoping is done (session 1, 2026-08-07) — see `DECISIONS.md` for full
rationale on each call:

1. **Shape:** both a Claude Code skill and a standalone CLI, sharing one
   core scan library (neither wrapper contains scan logic itself).
2. **v1 scope:** the full feature set below — known CVEs in declared
   dependencies, code-level red flags, a dependency-freshness signal,
   and a plain-language verdict.
3. **Discipline apparatus:** lightweight `PROJECT_DISCIPLINE.md` subset
   (see `CLAUDE.md` and `.agent/instructions.md`) — no live infra or
   external users yet, so no heavier apparatus.
4. **Public-repo plan:** MIT license, public from day one.

No code exists yet. Next up is Milestone #2 in `MILESTONES.md`: core
library skeleton, starting with a language/runtime choice that works
cleanly for both the skill and the CLI wrapper.
