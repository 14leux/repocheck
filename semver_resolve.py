#!/usr/bin/env python3
"""
RepoCheck -- npm version-range resolution.

Found by an independent adversarial QA subagent (not caught by the
session's own testing): `skeleton.py`'s package.json parser stripped
`^`/`~` prefixes and treated the remainder as if it were the exact
installed version, for BOTH CVE lookup and freshness classification.
Since most real npm manifests declare ranges rather than exact pins,
this wasn't an edge case -- it was wrong for the common case, and
produced a real DANGER verdict on `axios/axios` partly on that flawed
basis (the underlying CVE data itself was accurate; the confidence with
which a single version was implied was not).

This module resolves a declared range to the highest version currently
published that satisfies it, which is a materially better approximation
of "what actually gets installed" than the range's lower bound. It is
still an approximation -- the true installed version depends on the
npm/yarn/pnpm lockfile, which RepoCheck does not read (a further,
separate, and documented limitation, not fixed here) -- so every
resolution is labelled with whether it came from an exact pin or a
resolved range, never presented with false confidence.

No third-party semver library -- minimal caret/tilde comparison only,
consistent with the project's stdlib-only style so far. Ranges using
other operators (>=, <=, ||, x, *, workspace:, etc.) are honestly
reported as unresolvable rather than guessed at.
"""

import re


def _parse_version(v):
    """Returns (major, minor, patch) ints, or None if not parseable.
    Deliberately ignores pre-release/build metadata (e.g. "-beta.1") --
    documented limitation, not silently mishandled."""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


def _satisfies_caret(version, base):
    """npm caret semantics: ^1.2.3 := >=1.2.3 <2.0.0; ^0.2.3 := >=0.2.3
    <0.3.0; ^0.0.3 := >=0.0.3 <0.0.4 (leading zeroes lock more digits)."""
    v = _parse_version(version)
    b = _parse_version(base)
    if v is None or b is None:
        return False
    if v < b:
        return False
    if b[0] > 0:
        return v[0] == b[0]
    if b[1] > 0:
        return v[0] == 0 and v[1] == b[1]
    return v[0] == 0 and v[1] == 0 and v[2] == b[2]


def _satisfies_tilde(version, base):
    """~1.2.3 := >=1.2.3 <1.3.0 (patch-level changes only)."""
    v = _parse_version(version)
    b = _parse_version(base)
    if v is None or b is None:
        return False
    return v >= b and v[0] == b[0] and v[1] == b[1]


def resolve_npm_range(raw_version, available_versions):
    """
    Returns (resolved_version_or_None, is_exact_pin, note).

    - Exact version (no prefix, x.y.z): returned as-is, is_exact=True.
    - Caret/tilde range: resolved to the highest currently-published
      version satisfying it, is_exact=False, noted as a resolution.
    - Anything else (>=, <=, ||, x, *, workspace:, git URLs, etc.):
      resolution not attempted -- returns (None, False, "unresolvable"),
      caller must not silently treat this as "no dependency to check."
    """
    raw_version = raw_version.strip()

    if re.match(r"^\d+\.\d+\.\d+$", raw_version):
        return raw_version, True, "exact pin"

    if raw_version.startswith("^") or raw_version.startswith("~"):
        prefix, base = raw_version[0], raw_version[1:]
        satisfies = _satisfies_caret if prefix == "^" else _satisfies_tilde
        if _parse_version(base) is None:
            return None, False, f"unresolvable range: {raw_version!r}"
        candidates = [v for v in available_versions if satisfies(v, base)]
        if not candidates:
            return None, False, (
                f"range {raw_version!r} matched no currently-published version "
                f"(possible: base version itself was later unpublished)"
            )
        resolved = max(candidates, key=_parse_version)
        return resolved, False, f"resolved from range {raw_version!r} to latest matching {resolved}"

    return None, False, f"unresolvable range: {raw_version!r}"
