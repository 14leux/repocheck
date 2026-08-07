#!/usr/bin/env python3
"""
RepoCheck M6 -- severity model + humanized verdict.

Combines M2-M5 (CVE lookup, code red-flags, dependency freshness) or M3
(skill instruction scan) into one traffic-light signal plus a
plain-language narrative, per DECISIONS.md #009/#013/#015/#020.

Severity model (OI-008): every finding gets a severity weight
(critical=4, high=3, moderate=2, low=1). The overall verdict colour is
driven by the MAXIMUM weight found, never an average -- a single severe
finding must not be diluted by many clean signals (M6 acceptance
criterion, and the direct point of DECISION 013's rejection of a
single-score/grade output). Freshness findings ("pinned and abandoned")
contribute only a low weight and cannot push the verdict past caution on
their own -- an abandoned dependency is a risk signal, not evidence of
compromise.

Hardcoded, no interfaces yet (DECISIONS.md #021 -- extracted at M7).

Usage:
    python verdict.py repo owner/repo [--json]
    python verdict.py skill owner/repo path/to/SKILL.md [--json]
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from code_scan import RULESET_VERSION as CODE_SCAN_VERSION
from code_scan import iter_scan_targets, scan_file_content
from freshness_scan import RULESET_VERSION as FRESHNESS_SCAN_VERSION
from freshness_scan import FRESHNESS_LOOKUPS, classify
from skeleton import (
    InvalidRepoArgError,
    fetch_file,
    find_manifests,
    list_tree,
    osv_batch_query,
    parse_repo_arg,
)
from skill_scan import RULESET_VERSION as SKILL_SCAN_VERSION
from skill_scan import scan_skill_content
from suppression import apply_suppressions, load_suppressions

SEVERITY_WEIGHT = {"critical": 4, "high": 3, "moderate": 2, "low": 1}
COLOR_FOR_WEIGHT = {4: "DANGER", 3: "CAUTION", 2: "CAUTION", 1: "CAUTION", 0: "CLEAR"}

# --- plain-language explanations, per DECISION 009 ------------------------

EXPLANATIONS = {
    "cve": {
        "what": "a publicly known security flaw in this exact version of a dependency",
        "why": "attackers can look up the same public advisory and build an exploit "
               "against anyone still running the vulnerable version",
        "attack": "this is how many real breaches start -- not a custom hack, just "
                   "someone scanning for software still running a known-bad version",
    },
    "obfuscation": {
        "what": "code that decodes and runs a hidden payload at runtime instead of "
                "having its real behavior visible in the source",
        "why": "if you can't read what the code does, you can't tell it's malicious "
               "until it's already running",
        "attack": "malware commonly hides its real payload this way specifically so "
                   "a human skimming the source sees nothing alarming",
    },
    "credential-harvesting": {
        "what": "code that reads a sensitive file (like an SSH key or AWS "
                "credentials) and sends it somewhere over the network in the same "
                "place",
        "why": "this is the exact shape of a credential-theft attack -- read a "
               "secret, then exfiltrate it",
        "attack": "a compromised dependency or a malicious package does this to "
                   "steal your cloud credentials or SSH access without you noticing",
    },
    "suspicious-network-call": {
        "what": "code that talks to a raw IP address instead of a normal domain name",
        "why": "legitimate services almost always use a named domain; a bare IP is "
               "a common way to dodge domain-based security tools and block lists",
        "attack": "malware call-home traffic (\"beaconing\") is frequently pointed at "
                   "raw IPs for exactly this reason",
    },
    "suspicious-network-call-test-context": {
        "what": "a raw IP address, found in a file whose path looks like a test file",
        "why": "test fixtures commonly use well-known public IPs (DNS resolvers, "
               "example addresses) as sample data, not as something the running "
               "code actually calls out to",
        "attack": "low-priority signal -- worth a glance if you're auditing this "
                   "repo closely, not something that should drive the verdict on "
                   "its own",
    },
    "install-time-script": {
        "what": "a script that runs automatically when this package gets installed",
        "why": "install-time code runs with whatever permissions the install "
               "process has, often before anyone has reviewed what it does",
        "attack": "supply-chain attacks frequently use install hooks because they "
                   "execute without the victim ever running the package's real code",
    },
    "credential-exfiltration": {
        "what": "instructions in this skill that tell the agent to read a sensitive "
                "file and send its contents somewhere",
        "why": "an AI agent following these instructions has no way to tell they're "
               "malicious just from reading them -- they look like normal task steps",
        "attack": "this is the primary way malicious Claude Code skills steal "
                   "credentials: plain-English instructions, not obfuscated code",
    },
    "instruction-override": {
        "what": "phrasing that tries to make the agent discard its prior "
                "instructions or safety behavior",
        "why": "an agent that follows this could be redirected to do something the "
               "user never asked for",
        "attack": "this is a prompt-injection technique -- it doesn't need a "
                   "software bug, just wording the agent trusts by default",
    },
    "shell-pipe-execute": {
        "what": "an instruction that pipes downloaded content straight into a "
                "shell or interpreter",
        "why": "whatever that URL serves runs immediately and completely unreviewed "
               "-- and the content can be different every time it's fetched",
        "attack": "classic \"curl | bash\" supply-chain risk: what you audited and "
                   "what actually runs can be two different things",
    },
    "unresolvable-version-range": {
        "what": "a dependency declared with a version range RepoCheck could not resolve "
                "to one specific version (e.g. '>=1.2 <2.0', a git URL, or a workspace reference)",
        "why": "without knowing the actual installed version, RepoCheck cannot check it "
               "against known vulnerabilities -- this is a coverage gap, not a finding "
               "about the dependency itself",
        "attack": "not an attack signal -- a reminder that this scan's CVE coverage has a "
                   "blind spot here, worth checking manually",
    },
    "pinned and abandoned": {
        "what": "a dependency pinned to a version that hasn't been updated by its "
                "maintainer in years",
        "why": "an unmaintained dependency won't get a fix if a vulnerability is "
               "found in it later",
        "attack": "not an active attack on its own -- a risk-exposure signal, not "
                   "evidence of compromise",
    },
}


def osv_vuln_severity(vuln_id):
    url = f"https://api.osv.dev/v1/vulns/{vuln_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "repocheck-skeleton"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError:
        return "low"

    db_severity = data.get("database_specific", {}).get("severity")
    if db_severity:
        return db_severity.lower() if db_severity.lower() in SEVERITY_WEIGHT else "low"

    for sev in data.get("severity", []):
        score = sev.get("score", "")
        # crude CVSS-vector-to-bucket mapping: look for the base score if present
        m = re.search(r"/(\d\.\d)$", score) or re.search(r"^(\d+(?:\.\d+)?)$", score)
        if m:
            try:
                val = float(m.group(1))
                if val >= 9.0:
                    return "critical"
                if val >= 7.0:
                    return "high"
                if val >= 4.0:
                    return "moderate"
                return "low"
            except ValueError:
                pass
    return "moderate"  # unknown severity: assume moderate rather than silently low


def make_finding(category, severity, detail, source):
    exp = EXPLANATIONS.get(category, {"what": category, "why": "", "attack": ""})
    return {
        "category": category,
        "severity": severity,
        "detail": detail,
        "source": source,
        "what": exp["what"],
        "why": exp["why"],
        "attack_example": exp["attack"],
    }


def aggregate_color(findings):
    if not findings:
        return "CLEAR"
    max_weight = max(SEVERITY_WEIGHT[f["severity"]] for f in findings)
    return COLOR_FOR_WEIGHT[max_weight]


def render_findings(findings):
    if not findings:
        print("  none")
        return
    for f in findings:
        print(f"  [{f['severity'].upper()}] {f['category']} -- {f['detail']} (source: {f['source']})")
        print(f"      What this is: {f['what']}")
        if f["why"]:
            print(f"      Why it matters: {f['why']}")
        if f["attack_example"]:
            print(f"      Real-world pattern: {f['attack_example']}")


def repo_verdict(owner, repo, as_json):
    # pre-flight/progress text goes to stderr, never stdout -- stdout must
    # stay pure JSON when --json is passed (bug found and fixed in M6:
    # printing this to stdout corrupted --json's output)
    print(f"Pre-flight: scanning {owner}/{repo} (repo mode) -- CVE lookup, "
          f"code red-flag scan, dependency freshness. Static only, free, no LLM calls.",
          file=sys.stderr)

    # fetching the tree itself can fail (repo doesn't exist, GitHub is
    # down, rate-limited) -- found by independent QA: this previously
    # crashed uncaught before any of the pillar-level degraded-state
    # handling below even started. A scan that can't even list the
    # repo's files is maximally degraded, not a crash.
    try:
        tree = list_tree(owner, repo)
    except Exception as e:
        message = f"Could not list {owner}/{repo}'s files: {e}"
        if as_json:
            print(json.dumps({
                "repo": f"{owner}/{repo}", "mode": "repo", "verdict": "UNKNOWN",
                "findings": [], "suppressed": [],
                "scan_timestamp": datetime.now(timezone.utc).isoformat(),
                "degraded": [{"pillar": "repo-listing", "reason": message}],
            }, indent=2))
        else:
            print(f"\n** SCAN COULD NOT RUN -- {message} **")
            print("This is not a clean result. Check the repo name and try again.")
        return False  # found by independent QA: this previously exited 0,
        # indistinguishable from success to any script/CI checking exit code

    manifests = find_manifests(tree)
    candidate_files = list(iter_scan_targets(tree))
    scan_count = min(len(candidate_files), 300)  # code_scan.py's MAX_FILES_TO_SCAN

    # rough estimate from actual scope, not a static claim -- each of
    # these is roughly one sequential network call under current
    # implementation (no concurrency yet, KNOWLEDGE.md M6 finding)
    estimated_calls = len(manifests) + scan_count + len(manifests) * 2  # CVE+freshness proxy
    estimated_seconds = round(estimated_calls * 0.9)
    print(
        f"  Found {len(manifests)} manifest file(s), {len(candidate_files)} "
        f"candidate source file(s) ({scan_count} will be scanned). "
        f"Rough estimate: ~{estimated_seconds}s (sequential network calls, "
        f"no concurrency yet -- see OI-017/OI-019).\n",
        file=sys.stderr,
    )

    findings = []
    # DECISIONS.md-adjacent OI-011: a pillar that fails must say so in
    # the verdict, never silently look like "no findings" -- that's
    # indistinguishable from "verified clean" to a reader, which is a
    # worse failure mode than a scan that's just slow.
    degraded = []

    # --- manifest parsing + version resolution (shared by CVE + freshness) ---
    # npm ranges (^1.2.3, ~1.2.3) are resolved to the highest currently-
    # published matching version, never treated as if the range text
    # were an exact version -- found by independent QA: the earlier
    # version of this pillar stripped the ^/~ prefix and used the
    # result as a literal version, which is wrong for the common case
    # (most real package.json files declare ranges, not exact pins).
    # See semver_resolve.py.
    raw_packages = []
    resolved_packages = []
    unresolved_count = 0
    try:
        from skeleton import PARSERS, resolve_package_versions
        for path, ecosystem in manifests:
            filename = path.rsplit("/", 1)[-1]
            content = fetch_file(owner, repo, path)
            try:
                deps = PARSERS[filename](content)
            except Exception:
                continue
            for name, version in deps:
                raw_packages.append((name, version, ecosystem, path))

        resolved_packages = resolve_package_versions(raw_packages)
        unresolved_count = sum(1 for _, v, _, _, _, _ in resolved_packages if v is None)
    except Exception as e:
        degraded.append({"pillar": "manifest-parsing", "reason": str(e)})

    # --- CVE pillar ---
    try:
        checkable = [
            (name, version, eco, source, note)
            for name, version, eco, source, is_exact, note in resolved_packages
            if version is not None
        ]
        if checkable:
            results = osv_batch_query([(n, v, e) for n, v, e, _, _ in checkable])
            seen_severity = {}
            for (name, version, eco, source, note), result in zip(checkable, results):
                vulns = result.get("vulns", [])
                for v in vulns:
                    if v["id"] not in seen_severity:
                        seen_severity[v["id"]] = osv_vuln_severity(v["id"])
                    sev = seen_severity[v["id"]]
                    label = f"{name}=={version}" if note == "exact pin" else f"{name}=={version} ({note})"
                    findings.append(make_finding(
                        "cve", sev, f"{label} has known advisory {v['id']}", source,
                    ))
        if unresolved_count:
            findings.append(make_finding(
                "unresolvable-version-range", "low",
                f"{unresolved_count} dependencies declare a version range RepoCheck could not "
                f"resolve to a specific version -- NOT checked against OSV.dev, not assumed safe",
                "manifest",
            ))
    except Exception as e:
        degraded.append({"pillar": "cve", "reason": str(e)})

    # --- code red-flag pillar ---
    try:
        for path in iter_scan_targets(tree):
            try:
                content = fetch_file(owner, repo, path)
            except Exception:
                continue
            for category, fpath, line_no, detail in scan_file_content(path, content):
                sev = {
                    "obfuscation": "high",
                    "credential-harvesting": "critical",
                    "suspicious-network-call": "moderate",
                    "suspicious-network-call-test-context": "low",
                    "install-time-script": "moderate",
                }[category]
                findings.append(make_finding(category, sev, f"{fpath}:{line_no} -- {detail}", fpath))
    except Exception as e:
        degraded.append({"pillar": "code-red-flags", "reason": str(e)})

    # --- freshness pillar (capped severity contribution) ---
    # uses resolved_packages (real resolved versions), not raw_packages
    # -- a raw npm range like "^4.1.9" was never a real published
    # version to look up a release date for in the first place.
    abandoned_count = 0
    try:
        now = datetime.now(timezone.utc)
        for name, version, eco, source, is_exact, note in resolved_packages:
            if version is None:
                continue
            lookup = FRESHNESS_LOOKUPS.get(eco)
            if lookup is None:
                continue
            result = lookup(name, version)
            if result is None:
                continue
            latest, pinned_date, latest_date, _ = result
            status, days = classify(version, latest, pinned_date, latest_date, now)
            if status == "pinned and abandoned":
                abandoned_count += 1
                label = f"{name}=={version}" if is_exact else f"{name}=={version} ({note})"
                findings.append(make_finding(
                    "pinned and abandoned", "low",
                    f"{label}, last released {days} days ago", source,
                ))
    except Exception as e:
        degraded.append({"pillar": "freshness", "reason": str(e)})

    # --- suppression (OI-013) ---
    suppressions = load_suppressions(owner, repo)
    findings, suppressed = apply_suppressions(findings, suppressions)

    color = aggregate_color(findings)
    meta = {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "ruleset_versions": {
            "code_scan": CODE_SCAN_VERSION,
            "skill_scan": SKILL_SCAN_VERSION,
            "freshness_scan": FRESHNESS_SCAN_VERSION,
        },
        "degraded": degraded,
    }

    if as_json:
        print(json.dumps({
            "repo": f"{owner}/{repo}", "mode": "repo", "verdict": color,
            "findings": findings, "suppressed": suppressed, **meta,
        }, indent=2))
        return not degraded

    if degraded:
        print("** DEGRADED SCAN -- one or more pillars could not complete. "
              "Findings below are INCOMPLETE, not a clean result. **")
        for d in degraded:
            print(f"  [{d['pillar']}] {d['reason']}")
        print()

    print(f"VERDICT: {color}{'  (DEGRADED)' if degraded else ''}\n")
    print(f"Scanned: {meta['scan_timestamp']} | ruleset: code_scan={CODE_SCAN_VERSION}, "
          f"skill_scan={SKILL_SCAN_VERSION}, freshness_scan={FRESHNESS_SCAN_VERSION}\n")
    print("Findings:")
    render_findings(findings)
    if suppressed:
        print(f"\nSuppressed ({len(suppressed)}, per .repocheck-allow.json):")
        for f in suppressed:
            print(f"  [{f['category']}] {f['detail']} -- reason: {f['suppression_reason']}")
    if abandoned_count:
        print(f"\n({abandoned_count} dependencies are pinned to a version their "
              f"maintainer hasn't updated in years -- see 'pinned and abandoned' above.)")
    return not degraded


def skill_verdict(owner, repo, path, as_json):
    print(f"Pre-flight: scanning {owner}/{repo}:{path} (skill mode) -- static "
          f"instruction-content analysis. Free, no LLM calls, seconds.\n",
          file=sys.stderr)

    degraded = []
    findings = []
    caveats = []
    try:
        content = fetch_file(owner, repo, path)
        raw_findings, caveats = scan_skill_content(content)
        for category, detail in raw_findings:
            sev = {
                "credential-exfiltration": "critical",
                "instruction-override": "high",
                "shell-pipe-execute": "high",
            }[category]
            findings.append(make_finding(category, sev, detail, path))
    except Exception as e:
        degraded.append({"pillar": "skill-instruction-scan", "reason": str(e)})

    suppressions = load_suppressions(owner, repo)
    findings, suppressed = apply_suppressions(findings, suppressions)

    color = aggregate_color(findings)
    meta = {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "ruleset_versions": {"skill_scan": SKILL_SCAN_VERSION},
        "degraded": degraded,
    }

    if as_json:
        print(json.dumps({
            "repo": f"{owner}/{repo}", "path": path, "mode": "skill",
            "verdict": color, "findings": findings, "suppressed": suppressed,
            "caveats": [{"category": c, "detail": d} for c, d in caveats],
            **meta,
        }, indent=2))
        return not degraded

    if degraded:
        print("** DEGRADED SCAN -- could not complete. Result below is INCOMPLETE. **")
        for d in degraded:
            print(f"  [{d['pillar']}] {d['reason']}")
        print()

    print(f"VERDICT: {color}{'  (DEGRADED)' if degraded else ''}\n")
    print(f"Scanned: {meta['scan_timestamp']} | ruleset: skill_scan={SKILL_SCAN_VERSION}\n")
    print("Findings:")
    render_findings(findings)
    if suppressed:
        print(f"\nSuppressed ({len(suppressed)}, per .repocheck-allow.json):")
        for f in suppressed:
            print(f"  [{f['category']}] {f['detail']} -- reason: {f['suppression_reason']}")
    print()
    if caveats:
        print("Caveats (not findings -- things RepoCheck cannot fully verify by scanning):")
        for category, detail in caveats:
            print(f"  [{category}] {detail}")
    else:
        print("Caveats: none")
    return not degraded


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]

    if len(args) < 2:
        print("Usage: python verdict.py repo <owner/repo> [--json]")
        print("       python verdict.py skill <owner/repo> <path/to/SKILL.md> [--json]")
        sys.exit(1)

    mode = args[0]
    try:
        owner, repo = parse_repo_arg(args[1])
    except InvalidRepoArgError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if mode == "repo":
        repo_verdict(owner, repo, as_json)
    elif mode == "skill":
        if len(args) < 3:
            print("skill mode requires a path to SKILL.md")
            sys.exit(1)
        skill_verdict(owner, repo, args[2], as_json)
    else:
        print(f"Unknown mode: {mode!r} (expected 'repo' or 'skill')")
        sys.exit(1)


if __name__ == "__main__":
    main()
