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
import urllib.request
import tomllib

from github_provider import GitHubFileAccessProvider

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


def parse_repo_arg(arg):
    arg = arg.strip()
    if arg.startswith("http"):
        parts = arg.rstrip("/").split("/")
        return parts[-2], parts[-1]
    owner, repo = arg.split("/", 1)
    return owner, repo


def list_tree(owner, repo):
    return _provider.list_tree(owner, repo)


def fetch_file(owner, repo, path):
    return _provider.fetch_file(owner, repo, path)


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
    data = json.loads(content)
    result = []
    for section in ("dependencies", "devDependencies"):
        for name, version in data.get(section, {}).items():
            v = version.lstrip("^~=v ")
            if re.match(r"^\d+\.\d+\.\d+$", v):
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
        print("\nNo pinned dependencies found to check against OSV.dev.")
        return

    print(f"\nQuerying OSV.dev for {len(all_packages)} dependencies...\n")
    results = osv_batch_query([(n, v, e) for n, v, e, _ in all_packages])

    flagged = 0
    for (name, version, eco, source), result in zip(all_packages, results):
        vulns = result.get("vulns", [])
        if vulns:
            flagged += 1
            ids = ", ".join(v["id"] for v in vulns)
            print(
                f"  [VULNERABLE] {name}=={version} ({eco}, from {source}): "
                f"{len(vulns)} advisories — {ids}"
            )

    clean = len(all_packages) - flagged
    print(f"\n{flagged} of {len(all_packages)} dependencies have known advisories. {clean} clean.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python skeleton.py <owner/repo | github-url>")
        sys.exit(1)
    owner, repo = parse_repo_arg(sys.argv[1])
    scan(owner, repo)


if __name__ == "__main__":
    main()
