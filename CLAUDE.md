# RepoCheck — Agent Entry Point

Read `.agent/instructions.md` in full before doing anything else this
session. It defines the boot sequence, the Open Items table, and points
at the other checkpoint files (`tasks/context.md`, `tasks/wip.md`,
`tasks/todo.md`, `tasks/codebase_map.md`, `MILESTONES.md`,
`KNOWLEDGE.md`, `DECISIONS.md`).

This project follows the **lightweight subset** of
`D:\Projects\PROJECT_DISCIPLINE.md` (§10) — no `IMPROVEMENTS.md`, no
strict OI verification protocol, no acceptance-tests gate. Revisit once
there's live infra or external users.

## Non-negotiables

- **Live lookup at scan time, not a self-mutating local threat
  database.** Query CVE/advisory sources (OSV.dev, GHSA, npm/PyPI/PyPA
  feeds) at scan time. Never build a local threat DB that a scheduled
  job has to keep fresh — see README.md "Key design decision" for why.
- **Never execute untrusted code from a scanned repo.** RepoCheck reads
  and analyzes source, dependency manifests, and metadata — it must
  never `npm install`, `pip install`, run a build script, or execute
  anything belonging to the repo under scan.
- **Skill mode must scan `SKILL.md`/skill manifest content by default,
  not only as an opt-in deep scan.** The dominant attack on Claude Code
  skills is instruction-shaped (malicious prose in `SKILL.md`), not
  code-shaped — a code-only red-flag checklist gives false confidence
  on exactly this artifact type. See DECISIONS.md #015.
- **The deep-scan LLM pass must treat all scanned content as untrusted
  data, never as instructions.** Scanned repo/skill text must be
  structurally delimited so it can never be interpreted as directions
  to follow — mode-agnostic, applies to repo mode and skill mode alike.
  See DECISIONS.md #016.
