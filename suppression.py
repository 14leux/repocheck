#!/usr/bin/env python3
"""
RepoCheck M11 -- suppression mechanism (OI-013).

A repo (or the user running the scan) can mark a specific finding as
reviewed-and-accepted via a `.repocheck-allow.json` file in the
scanned repo's root: a list of {"category", "path", "reason"} entries.
`path` matches by substring against the finding's `source` field, so
one entry can cover a whole file without needing an exact line number.

This is distinct from a rule-level fix (like the private-IP exclusion
or the descriptive-context guard added earlier this session) -- those
fix a rule for everyone. This is for a specific finding a specific repo
maintainer has actually reviewed and judged safe for their case, with a
reason recorded so it's a decision, not a silent gap.

Missing or malformed suppression files are treated as "no suppressions"
-- never an error that blocks the scan.
"""

import json


def load_suppressions(owner, repo, path=".repocheck-allow.json"):
    from skeleton import fetch_file
    try:
        content = fetch_file(owner, repo, path)
    except Exception:
        return []
    try:
        entries = json.loads(content)
    except json.JSONDecodeError:
        return []
    if not isinstance(entries, list):
        return []
    # found by independent QA: checking required keys are present isn't
    # enough -- a wrong-TYPE value (e.g. "path": 123) passed this check
    # and then crashed apply_suppressions with a TypeError, contradicting
    # this module's own "never blocks the scan" guarantee. Every field
    # must be a string, not just present.
    return [
        e for e in entries
        if isinstance(e, dict)
        and {"category", "path", "reason"} <= e.keys()
        and all(isinstance(e[k], str) for k in ("category", "path", "reason"))
    ]


def apply_suppressions(findings, suppressions):
    """Returns (kept_findings, suppressed_findings). Suppressed findings
    keep all their original fields plus 'suppression_reason', so they
    can still be shown (not hidden) with the reason attached."""
    kept, suppressed = [], []
    for f in findings:
        match = next(
            (s for s in suppressions
             if s["category"] == f["category"] and s["path"] in f.get("source", "")),
            None,
        )
        if match:
            suppressed.append({**f, "suppression_reason": match["reason"]})
        else:
            kept.append(f)
    return kept, suppressed
