## Not started — first session should scope, not just build

- [ ] Decide: Claude Code skill only, vs. standalone repo/CLI/service
- [ ] Decide concretely what "safe" checks for (start narrow: known CVEs in
      declared dependencies + a short list of code red flags — not
      everything on day one)
- [ ] Decide how much of `PROJECT_DISCIPLINE.md`'s apparatus this project
      needs on day one (lightweight subset is the default per its §10 —
      revisit once there's live infra or external users)
- [ ] Decide the public-repo plan: license, contribution model, distribution
      (Claude Code plugin/marketplace skill, standalone CLI, or both)
- [ ] Confirm the "live lookup, not self-mutating local DB" design decision
      still holds once real scoping starts (see README.md — this was
      decided in the originating conversation, not yet pressure-tested)
