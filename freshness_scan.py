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
)

ABANDONED_THRESHOLD_DAYS = 730  # ~2 years since the package's own latest release


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "repocheck-skeleton"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


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


FRESHNESS_LOOKUPS = {
    "PyPI": pypi_freshness,
    "npm": npm_freshness,
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

    print(f"Checking freshness for {len(packages)} dependencies...\n")
    for name, version, eco, source in packages:
        lookup = FRESHNESS_LOOKUPS.get(eco)
        if lookup is None:
            summary["unknown"] += 1
            continue
        result = lookup(name, version)
        if result is None:
            summary["unknown"] += 1
            continue
        latest, pinned_date, latest_date, versions_behind = result
        status, days_since_latest = classify(version, latest, pinned_date, latest_date, now)
        summary[status] += 1
        if status != "current":
            print(
                f"  [{status}] {name}=={version} ({eco}) -- {versions_behind} version(s) "
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
