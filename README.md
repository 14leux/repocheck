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

## Scope for the first real session

Not built yet — this folder exists only to hold the idea so it isn't lost.
First session should decide, in order:
1. Skill-only (runs inside Claude Code, no standalone infra) vs. a real
   standalone repo/CLI/service — this changes almost everything downstream.
2. What "safe" actually checks for, concretely — start narrow (known CVEs
   in declared dependencies + a short list of code red flags) rather than
   trying to cover everything on day one.
3. Whether this project needs the full `PROJECT_DISCIPLINE.md` apparatus
   (see `D:\Projects\PROJECT_DISCIPLINE.md`) or the lightweight subset —
   given it's day one with nothing built, lightweight is right for now;
   revisit once there's live infra or external users (the stated trigger
   in that doc's §10).
4. Public-repo plan: license, contribution model, and whether it ships as
   a Claude Code plugin/marketplace skill, a standalone CLI, or both.
