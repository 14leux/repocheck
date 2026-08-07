#!/usr/bin/env python3
"""
RepoCheck M2 walking skeleton.

Hardcoded to GitHub + OSV.dev, no abstractions. Proves the CVE-lookup
mechanism against a real repo before any interface gets designed around
it (DECISIONS.md #021). Gets refactored behind the pluggable
file-access/model-provider interfaces at M7 — this file is not meant to
survive that refactor unchanged.

Reads a repo's dependency manifests via the GitHub contents API and
never clones, installs, or executes anything belonging to the scanned
repo (CLAUDE.md non-negotiable).

Usage:
    python skeleton.py owner/repo
    python skeleton.py https://github.com/owner/repo

Set GITHUB_TOKEN to avoid GitHub's low unauthenticated rate limit.
"""

import json
import re
import sys
import urllib.error
import urllib.request
import tomllib

from github_provider import GitHubFileAccessProvider
from semver_resolve import resolve_npm_range

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OSV_API = "https://api.osv.dev/v1/querybatch"

# manifest filename -> ecosystem name OSV.dev expects
MANIFEST_ECOSYSTEMS = {
    "pyproject.toml": "PyPI",
    "requirements.txt": "PyPI",
    "package.json": "npm",
    "go.mod": "Go",
}

# module-level default provider (DECISIONS.md #012/#021) -- every other
# script in this project imports list_tree/fetch_file from here, so
# swapping the provider here swaps it everywhere with zero changes to
# skill_scan.py, code_scan.py, freshness_scan.py, or verdict.py. See
# swap_provider() and test_provider_swap.py for the M7 acceptance-
# criteria demonstration.
_provider = GitHubFileAccessProvider()


def swap_provider(provider):
    """Swap the active FileAccessProvider. Used by test_provider_swap.py
    to demonstrate M7's acceptance criterion: adding a second
    implementation requires no change to any calling code."""
    global _provider
    _provider = provider


class InvalidRepoArgError(ValueError):
    pass


def strip_invisible_characters(content):
    """
    Removes Unicode "format" category characters (zero-width space,
    zero-width joiner/non-joiner, word joiner, BOM, etc.) before any
    pattern matching runs. Shared by skill_scan.py and code_scan.py --
    a general normalization step, not specific to either.

    Found via OI-016 research (Snyk's ToxicSkills audit, Feb 2026):
    SKILL.md files can conceal adversarial instructions by inserting
    invisible Unicode characters mid-word (e.g. "i<ZWSP>g<ZWSP>n<ZWSP>ore"),
    which breaks every `\\b...\\b`-anchored regex while a human or an
    LLM reading the rendered text sees ordinary words with nothing
    visibly wrong. A fix at the normalization layer closes this for
    every pattern at once, rather than teaching each individual regex
    to tolerate invisible characters.
    """
    import unicodedata
    return "".join(c for c in content if unicodedata.category(c) != "Cf")


def parse_repo_arg(arg):
    """
    Raises InvalidRepoArgError with a clear, actionable message on bad
    input, rather than letting a bare split()/unpack crash with a raw
    traceback -- found by independent QA: "justarepo" and "" both
    previously crashed uncaught in the CLI.

    A second independent QA pass found the first version of this fix was
    itself too loose: "owner/" gave a wrong error message (said "missing
    the owner" when it was the repo that was missing/empty), "owner//repo"
    and "owner/repo/extra/path" were silently accepted with a malformed
    repo name instead of erroring, and a GitHub URL missing the repo
    segment ("https://github.com/owner") silently misparsed "github.com"
    as the owner. Rewritten to validate strictly: the non-URL form must
    be exactly one "owner/repo" pair, no more, no fewer segments; the URL
    form requires github.com followed by exactly two path segments.
    """
    arg = arg.strip()
    if not arg:
        raise InvalidRepoArgError("empty repo argument -- expected 'owner/repo' or a GitHub URL")

    if arg.startswith("http"):
        m = re.search(r"github\.com/([^/]+)/([^/]+)", arg)
        if not m or not m.group(1) or not m.group(2):
            raise InvalidRepoArgError(
                f"could not find an owner/repo pair in URL: {arg!r} "
                f"(expected e.g. https://github.com/owner/repo)"
            )
        return m.group(1), m.group(2)

    parts = arg.rstrip("/").split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise InvalidRepoArgError(
            f"{arg!r} is not a valid 'owner/repo' -- expected exactly one slash, "
            f"e.g. 'pallets/itsdangerous' (a path within the repo goes in a "
            f"separate argument, not appended here)"
        )
    return parts[0], parts[1]


def list_tree(owner, repo):
    return _provider.list_tree(owner, repo)


def fetch_file(owner, repo, path):
    return _provider.fetch_file(owner, repo, path)


def fetch_all_files(owner, repo, paths):
    """OI-017: bulk fetch, one call instead of one-per-file where the
    active provider supports it (GitHubFileAccessProvider uses a
    tarball download). Returns {path: content_or_Exception}."""
    return _provider.fetch_all_files(owner, repo, paths)


def find_manifests(tree):
    found = []
    for entry in tree:
        if entry["type"] != "blob":
            continue
        name = entry["path"].rsplit("/", 1)[-1]
        if name in MANIFEST_ECOSYSTEMS:
            found.append((entry["path"], MANIFEST_ECOSYSTEMS[name]))
    return found


def parse_pyproject(content):
    data = tomllib.loads(content)
    deps = data.get("project", {}).get("dependencies", [])
    result = []
    for dep in deps:
        dep = dep.split(";")[0].strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*==\s*([A-Za-z0-9_.\-]+)$", dep)
        if m:
            result.append((m.group(1), m.group(2)))
    return result


def parse_requirements_txt(content):
    result = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*==\s*([A-Za-z0-9_.\-]+)", line)
        if m:
            result.append((m.group(1), m.group(2)))
    return result


def parse_package_json(content):
    """
    Returns (name, raw_version) with the range prefix (^, ~, or none)
    kept INTACT -- earlier versions of this parser stripped it and
    treated a caret/tilde range as an exact version, which is wrong for
    the common case (found by independent QA, see semver_resolve.py).
    Callers must resolve the range before treating it as one version;
    see resolve_package_versions() below.
    """
    data = json.loads(content)
    result = []
    for section in ("dependencies", "devDependencies"):
        for name, version in data.get(section, {}).items():
            v = version.strip()
            if re.match(r"^[\^~]?\d+\.\d+\.\d+", v):
                result.append((name, v))
    return result


def parse_go_mod(content):
    result = []
    in_require_block = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require ("):
            in_require_block = True
            continue
        if in_require_block and line == ")":
            in_require_block = False
            continue
        m = None
        if in_require_block:
            m = re.match(r"^([\w./-]+)\s+v([\d.]+)", line)
        elif line.startswith("require "):
            m = re.match(r"^require\s+([\w./-]+)\s+v([\d.]+)", line)
        if m:
            result.append((m.group(1), m.group(2)))
    return result


PARSERS = {
    "pyproject.toml": parse_pyproject,
    "requirements.txt": parse_requirements_txt,
    "package.json": parse_package_json,
    "go.mod": parse_go_mod,
}


def fetch_npm_versions(name):
    req = urllib.request.Request(
        f"https://registry.npmjs.org/{name}", headers={"User-Agent": "repocheck-skeleton"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError:
        return []
    return list(data.get("versions", {}).keys())


def resolve_package_versions(packages):
    """
    packages: list of (name, raw_version, ecosystem, source).
    Returns list of (name, resolved_version_or_None, ecosystem, source,
    is_exact, note).

    PyPI/Go parsers already emit exact versions (`==`/`vX.Y.Z` matching
    only), passed through unchanged. npm's parser keeps range prefixes
    intact (fixed as part of this session's caret-range bug fix), so
    npm packages get resolved against the live registry here -- to the
    highest currently-published version satisfying the range, never
    silently treated as if the range's text were an exact version.

    This is still an approximation of what's actually installed (the
    true answer lives in a lockfile RepoCheck doesn't read) -- every
    result carries is_exact/note so callers can represent that honestly
    rather than with false confidence.
    """
    from concurrency import parallel_map

    resolved = []
    npm_names = sorted({name for name, _, eco, _ in packages if eco == "npm"})
    # one registry fetch per unique npm package name, all concurrent
    # rather than one at a time (OI-019)
    version_lists = parallel_map(fetch_npm_versions, npm_names)
    npm_version_cache = {
        name: (versions if not isinstance(versions, Exception) else [])
        for name, versions in zip(npm_names, version_lists)
    }

    for name, raw_version, ecosystem, source in packages:
        if ecosystem != "npm":
            resolved.append((name, raw_version, ecosystem, source, True, "exact pin"))
            continue
        version, is_exact, note = resolve_npm_range(raw_version, npm_version_cache[name])
        resolved.append((name, version, ecosystem, source, is_exact, note))
    return resolved


def osv_batch_query(packages):
    """packages: list of (name, version, ecosystem)"""
    queries = [
        {"package": {"name": name, "ecosystem": eco}, "version": version}
        for name, version, eco in packages
    ]
    body = json.dumps({"queries": queries}).encode()
    req = urllib.request.Request(
        OSV_API, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["results"]


def scan(owner, repo):
    print(f"Scanning {owner}/{repo}\n")
    tree = list_tree(owner, repo)
    manifests = find_manifests(tree)
    if not manifests:
        print("No recognized manifest files found.")
        return

    print(f"Found {len(manifests)} manifest file(s):")
    for path, eco in manifests:
        print(f"  {path} ({eco})")

    all_packages = []  # (name, version, ecosystem, source_path)
    print()
    for path, ecosystem in manifests:
        filename = path.rsplit("/", 1)[-1]
        parser = PARSERS[filename]
        content = fetch_file(owner, repo, path)
        try:
            deps = parser(content)
        except Exception as e:
            print(f"  Could not parse {path}: {e}")
            continue
        print(f"  {path}: {len(deps)} pinned dependencies recognized")
        for name, version in deps:
            all_packages.append((name, version, ecosystem, path))

    if not all_packages:
        print("\nNo dependencies found to check against OSV.dev.")
        return

    resolved = resolve_package_versions(all_packages)
    checkable = [(n, v, e, s, note) for n, v, e, s, is_exact, note in resolved if v is not None]
    unresolved = [(n, e, note) for n, v, e, s, is_exact, note in resolved if v is None]
    if unresolved:
        print(f"  {len(unresolved)} dependencies use a version range RepoCheck "
              f"could not resolve -- NOT checked, not silently assumed safe:")
        for name, eco, note in unresolved:
            print(f"    {name} ({eco}): {note}")

    if not checkable:
        print("\nNo resolvable dependency versions to check against OSV.dev.")
        return

    print(f"\nQuerying OSV.dev for {len(checkable)} dependencies...\n")
    results = osv_batch_query([(n, v, e) for n, v, e, _, _ in checkable])

    flagged = 0
    for (name, version, eco, source, note), result in zip(checkable, results):
        vulns = result.get("vulns", [])
        if vulns:
            flagged += 1
            ids = ", ".join(v["id"] for v in vulns)
            label = f"{name}=={version}" if note == "exact pin" else f"{name}=={version} ({note})"
            print(
                f"  [VULNERABLE] {label} ({eco}, from {source}): "
                f"{len(vulns)} advisories — {ids}"
            )

    clean = len(checkable) - flagged
    print(f"\n{flagged} of {len(checkable)} checked dependencies have known advisories. "
          f"{clean} clean. ({len(unresolved)} not checked -- unresolvable version range.)")


def main():
    if len(sys.argv) != 2:
        print("Usage: python skeleton.py <owner/repo | github-url>")
        sys.exit(1)
    owner, repo = parse_repo_arg(sys.argv[1])
    scan(owner, repo)


if __name__ == "__main__":
    main()
