#!/usr/bin/env python3
"""
RepoCheck M8 -- CLI wrapper. `repocheck <target>` is the first
genuinely usable release; V1 is done when this works.

Contains no scan logic of its own (DECISIONS.md #002) -- everything
here is argument parsing, mode auto-detection, and a call into
verdict.py's repo_verdict()/skill_verdict().

Usage:
    python repocheck.py owner/repo
    python repocheck.py https://github.com/owner/repo
    python repocheck.py https://github.com/owner/repo/blob/main/skills/x/SKILL.md
    python repocheck.py owner/repo path/to/SKILL.md
    python repocheck.py owner/repo --mode skill --path path/to/SKILL.md
    (any of the above + --json)
"""

import re
import sys

from skeleton import InvalidRepoArgError, parse_repo_arg
from verdict import repo_verdict, skill_verdict

GITHUB_BLOB_PATTERN = r"github\.com/([^/]+)/([^/]+)/blob/[^/]+/(.+)$"


def detect_target(args):
    """
    Returns (mode, owner, repo, skill_path_or_None).

    Auto-detection, in order:
    1. A full GitHub blob URL pointing at a file -- skill mode, path
       extracted from the URL. Paste a skill's GitHub link, it just works.
    2. A second positional argument given -- skill mode, that argument
       is the path.
    3. Otherwise -- repo mode.
    An explicit --mode flag always wins over auto-detection.
    """
    explicit_mode = None
    if "--mode" in args:
        i = args.index("--mode")
        explicit_mode = args[i + 1]
        del args[i:i + 2]

    explicit_path = None
    if "--path" in args:
        i = args.index("--path")
        explicit_path = args[i + 1]
        del args[i:i + 2]

    target = args[0]
    m = re.search(GITHUB_BLOB_PATTERN, target)
    if m:
        owner, repo, path = m.group(1), m.group(2), m.group(3)
        mode = explicit_mode or "skill"
        return mode, owner, repo, (explicit_path or path)

    owner, repo = parse_repo_arg(target)
    path = explicit_path or (args[1] if len(args) > 1 else None)
    mode = explicit_mode or ("skill" if path else "repo")
    return mode, owner, repo, path


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]

    if not args:
        print(__doc__)
        sys.exit(1)

    # top-level guard: no scan-related error should ever surface as a raw
    # Python traceback to a CLI user. Found by independent QA -- a typo'd
    # or nonexistent repo previously crashed uncaught here.
    try:
        mode, owner, repo, path = detect_target(args)

        if mode == "repo":
            ok = repo_verdict(owner, repo, as_json)
        elif mode == "skill":
            if not path:
                print("skill mode needs a path to SKILL.md (paste a GitHub blob URL, "
                      "pass it as a second argument, or use --path)")
                sys.exit(1)
            ok = skill_verdict(owner, repo, path, as_json)
        else:
            print(f"Unknown mode: {mode!r} (expected 'repo' or 'skill')")
            sys.exit(1)
    except InvalidRepoArgError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # found by independent QA: a degraded/failed scan previously exited 0,
    # indistinguishable from success to any script or CI checking the
    # exit code -- exit code reflects whether the scan completed
    # reliably, not the security verdict color itself.
    if ok is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
