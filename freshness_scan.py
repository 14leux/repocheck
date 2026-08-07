#!/usr/bin/env python3
"""
RepoCheck M5 -- dependency freshness signal.

How far behind each declared dependency is. Deliberately distinguishes
two things that are easy to conflate: whether a dependency is pinned to
an exact version (a packaging style choice, not a risk signal on its
own) and whether the package itself looks abandoned (a real risk
signal). `browser-use` pins every dependency exactly -- that must not,
on its own, read as stale (M5 acceptance criterion).

Sources: PyPI's JSON API and npm's registry API, both free and
unauthenticated, matching the ecosystems already exercised by M2/M4.
Go support is a known gap (OI-018) -- the module proxy's version-listing
API needs case-encoding handling for module paths with uppercase
letters, not implemented here.

Hardcoded, no interfaces yet (DECISIONS.md #021 -- extracted at M7).

Usage:
    python freshness_scan.py owner/repo
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from skeleton import (
    PARSERS,
    fetch_file,
    find_manifests,
    list_tree,
    parse_repo_arg,
    resolve_package_versions,
)

# bumped whenever ABANDONED_THRESHOLD_DAYS or the classification logic
# changes (DECISIONS.md #012 -- flagged as missing by independent QA)
RULESET_VERSION = "freshness_scan-2026-08-07"

ABANDONED_THRESHOLD_DAYS = 730  # ~2 years since the package's own latest release


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "repocheck-skeleton"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def http_get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "repocheck-skeleton"})
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


def encode_go_module_path(path):
    """Go module proxy 'case encoding': every uppercase letter becomes
    '!' + its lowercase form (e.g. github.com/Owner/Repo ->
    github.com/!owner/!repo), documented at
    https://go.dev/ref/mod#module-proxy -- this was the specific gap
    OI-018 named (Go freshness lookup not implemented because of this
    encoding requirement)."""
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), path)


def parse_date(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def pypi_freshness(name, pinned_version):
    try:
        data = http_get_json(f"https://pypi.org/pypi/{name}/json")
    except urllib.error.HTTPError:
        return None
    latest = data["info"]["version"]
    releases = data.get("releases", {})

    def first_upload(version):
        files = releases.get(version, [])
        dates = [f["upload_time_iso_8601"] for f in files if "upload_time_iso_8601" in f]
        return parse_date(min(dates)) if dates else None

    pinned_date = first_upload(pinned_version)
    latest_date = first_upload(latest)
    if pinned_date is None or latest_date is None:
        return None

    versions_behind = sum(
        1 for v in releases if (d := first_upload(v)) and d > pinned_date
    )
    return latest, pinned_date, latest_date, versions_behind


def npm_freshness(name, pinned_version):
    try:
        data = http_get_json(f"https://registry.npmjs.org/{name}")
    except urllib.error.HTTPError:
        return None
    latest = data.get("dist-tags", {}).get("latest")
    times = data.get("time", {})
    pinned_date_s = times.get(pinned_version)
    latest_date_s = times.get(latest) if latest else None
    if not pinned_date_s or not latest_date_s:
        return None

    pinned_date = parse_date(pinned_date_s)
    latest_date = parse_date(latest_date_s)
    versions_behind = sum(
        1
        for v, d in times.items()
        if v not in ("created", "modified") and parse_date(d) > pinned_date
    )
    return latest, pinned_date, latest_date, versions_behind


def go_freshness(name, pinned_version):
    encoded = encode_go_module_path(name)
    pinned_version_str = pinned_version if pinned_version.startswith("v") else f"v{pinned_version}"

    try:
        latest_data = http_get_json(f"https://proxy.golang.org/{encoded}/@latest")
        pinned_data = http_get_json(f"https://proxy.golang.org/{encoded}/@v/{pinned_version_str}.info")
    except urllib.error.HTTPError:
        return None

    latest = latest_data.get("Version")
    latest_time_s = latest_data.get("Time")
    pinned_time_s = pinned_data.get("Time")
    if not latest or not latest_time_s or not pinned_time_s:
        return None

    latest_date = parse_date(latest_time_s)
    pinned_date = parse_date(pinned_time_s)

    # versions_behind is a courtesy count, not load-bearing for
    # classify() (which only needs the two dates + version strings) --
    # approximated via string sort of @v/list rather than fetching every
    # version's own .info (would be one more HTTP call per version).
    # Documented as an approximation, not exact chronological ordering.
    try:
        listing = http_get_text(f"https://proxy.golang.org/{encoded}/@v/list")
        all_versions = sorted(v.strip() for v in listing.splitlines() if v.strip())
        versions_behind = sum(1 for v in all_versions if v > pinned_version_str)
    except urllib.error.HTTPError:
        versions_behind = 0

    return latest, pinned_date, latest_date, versions_behind


FRESHNESS_LOOKUPS = {
    "PyPI": pypi_freshness,
    "npm": npm_freshness,
    "Go": go_freshness,
}


def classify(pinned_version, latest_version, pinned_date, latest_date, now):
    """
    Abandonment is a property of the package (how long since anyone
    released anything), checked first and independent of whether the
    pin happens to equal "latest" -- a package whose only release was
    11 years ago is "latest" by definition and still abandoned. Being
    pinned to that latest version does not make it current.
    """
    days_since_latest_release = (now - latest_date).days
    days_behind = (latest_date - pinned_date).days

    if days_since_latest_release > ABANDONED_THRESHOLD_DAYS:
        return "pinned and abandoned", days_since_latest_release
    if pinned_version == latest_version or days_behind <= 0:
        return "current", days_since_latest_release
    return "behind, actively maintained", days_since_latest_release


def scan(owner, repo):
    print(f"Scanning {owner}/{repo} (dependency freshness)\n")
    tree = list_tree(owner, repo)
    manifests = find_manifests(tree)
    if not manifests:
        print("No recognized manifest files found.")
        return

    packages = []  # (name, version, ecosystem, source_path)
    for path, ecosystem in manifests:
        filename = path.rsplit("/", 1)[-1]
        content = fetch_file(owner, repo, path)
        try:
            deps = PARSERS[filename](content)
        except Exception as e:
            print(f"  Could not parse {path}: {e}")
            continue
        for name, version in deps:
            packages.append((name, version, ecosystem, path))

    now = datetime.now(timezone.utc)
    summary = {"current": 0, "behind, actively maintained": 0, "pinned and abandoned": 0, "unknown": 0}

    # npm ranges get resolved to a real published version first -- a raw
    # "^4.1.9" was never a real version to look up a release date for
    # (independent-QA-found bug, see semver_resolve.py)
    resolved = resolve_package_versions(packages)
    unresolved = sum(1 for _, v, _, _, _, _ in resolved if v is None)

    print(f"Checking freshness for {len(resolved) - unresolved} resolvable of "
          f"{len(resolved)} dependencies "
          f"({unresolved} use an unresolvable version range)...\n")

    # OI-019: was fully sequential here too (only verdict.py's inline
    # pillar had been parallelized) -- one HTTP call per dependency,
    # concurrent rather than one at a time.
    from concurrency import parallel_map
    checkable = [
        (name, version, eco, source, is_exact, note)
        for name, version, eco, source, is_exact, note in resolved
        if version is not None and eco in FRESHNESS_LOOKUPS
    ]
    for name, version, eco, source, is_exact, note in resolved:
        if version is not None and eco not in FRESHNESS_LOOKUPS:
            summary["unknown"] += 1

    def lookup_one(pkg):
        name, version, eco, source, is_exact, note = pkg
        return FRESHNESS_LOOKUPS[eco](name, version)

    lookup_results = parallel_map(lookup_one, checkable)
    for (name, version, eco, source, is_exact, note), result in zip(checkable, lookup_results):
        if result is None or isinstance(result, Exception):
            summary["unknown"] += 1
            continue
        latest, pinned_date, latest_date, versions_behind = result
        status, days_since_latest = classify(version, latest, pinned_date, latest_date, now)
        summary[status] += 1
        label = f"{name}=={version}" if is_exact else f"{name}=={version} ({note})"
        if status != "current":
            print(
                f"  [{status}] {label} ({eco}) -- {versions_behind} version(s) "
                f"newer exist, latest is {latest} (released {days_since_latest} days ago)"
            )

    print("\nRepo-level summary:")
    for status, count in summary.items():
        print(f"  {status}: {count}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python freshness_scan.py <owner/repo>")
        sys.exit(1)
    owner, repo = parse_repo_arg(sys.argv[1])
    scan(owner, repo)


if __name__ == "__main__":
    main()
