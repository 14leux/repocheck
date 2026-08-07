#!/usr/bin/env python3
"""
RepoCheck M4 — repo-mode code red-flag scan.

Static checklist over fetched source: obfuscation, suspicious network
calls, credential-harvesting patterns, install-time scripts. Fetches raw
file content and pattern-matches locally — does NOT depend on GitHub's
hosted code-search API, which gave unreliable results during the M1
validation trace (OI-015).

Streams: processes one file's content at a time and discards it before
fetching the next, so memory use does not grow with repo size (M4
acceptance criterion). API-call count still scales with file count —
one GitHub contents-API call per matched file — which is a known,
recorded scaling gap for very large repos (OI-017), separate from the
memory concern this milestone targets.

Hardcoded, no interfaces yet (DECISIONS.md #021 — extracted at M7).

Usage:
    python code_scan.py owner/repo
"""

import ipaddress
import re
import sys

from skeleton import fetch_file, list_tree, parse_repo_arg

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".rb", ".go"}
INSTALL_MANIFEST_FILES = {"setup.py", "package.json", "pyproject.toml"}

# cap on files fetched per scan -- API-call count scales with file count,
# not yet solved for very large repos (OI-017). Capped rather than
# silently scanning forever.
MAX_FILES_TO_SCAN = 300

# --- obfuscation --------------------------------------------------------

OBFUSCATION_PATTERNS = [
    r"\b(eval|exec)\s*\(\s*(base64\.b64decode|codecs\.decode|bytes\.fromhex)",
    r"\bexec\s*\(\s*compile\s*\(",
    r"['\"][A-Za-z0-9+/]{200,}={0,2}['\"]",  # long base64-looking blob
]

# --- credential harvesting (co-occurrence, same limitation as skill_scan) ---

SENSITIVE_PATH_PATTERNS = [
    r"~/\.ssh", r"id_rsa", r"id_ed25519", r"\.aws/credentials",
    r"\.aws/config", r"\.npmrc", r"\.pypirc", r"\.netrc",
    r"/etc/passwd", r"\.env\b", r"\.git-credentials",
]

NETWORK_SEND_PATTERNS = [
    r"\bcurl\s+.*-X\s*POST", r"\brequests\.post\(",
    r"\bfetch\([^)]*\)\s*\.then", r"\burllib\.request\.urlopen\(",
    r"\bsocket\.socket\(",
]

# --- suspicious network calls -------------------------------------------

RAW_IP_URL_PATTERN = r"https?://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

# a repo full of test files targeting this pattern (browser-use's own
# tests/ci/security/test_ip_blocking.py) found the gap this closes: a
# raw private/loopback/reserved IP can never be a real exfiltration
# destination for an external attacker, so flagging it is pure noise --
# not a scope-based suppression of "test files," a correctness fix on
# the rule itself (KNOWLEDGE.md, M6 session).
TEST_PATH_PATTERN = r"(^|/)(tests?|spec)(/|$)|test_[^/]+\.py$|_test\.py$"


def is_private_or_reserved_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local

# --- install-time scripts, keyed by filename ----------------------------

INSTALL_HOOK_PATTERNS = {
    "package.json": [r'"(pre|post)install"\s*:'],
    "setup.py": [r"cmdclass\s*="],
    "pyproject.toml": [r"\[tool\.\w+\.(hooks|build-hooks)\]"],
}


def find_matches(content, patterns):
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, content, re.IGNORECASE):
            line_no = content.count("\n", 0, m.start()) + 1
            hits.append((line_no, m.group(0)[:80].strip()))
    return hits


def scan_file_content(path, content):
    findings = []
    filename = path.rsplit("/", 1)[-1]

    for line_no, text in find_matches(content, OBFUSCATION_PATTERNS):
        findings.append(("obfuscation", path, line_no, text))

    sensitive_hits = find_matches(content, SENSITIVE_PATH_PATTERNS)
    network_hits = find_matches(content, NETWORK_SEND_PATTERNS)
    if sensitive_hits and network_hits:
        findings.append((
            "credential-harvesting", path, sensitive_hits[0][0],
            f"references {sensitive_hits[0][1]} and sends over network ({network_hits[0][1]}) in the same file",
        ))

    is_test_path = bool(re.search(TEST_PATH_PATTERN, path, re.IGNORECASE))
    for m in re.finditer(RAW_IP_URL_PATTERN, content, re.IGNORECASE):
        ip_str = m.group(1)
        if is_private_or_reserved_ip(ip_str):
            continue  # never a real exfiltration destination -- correctness fix, not suppression
        line_no = content.count("\n", 0, m.start()) + 1
        text = m.group(0)
        if is_test_path:
            # a real public IP, but inside a path that looks like a test
            # file -- likely example/fixture data (e.g. 8.8.8.8 as a
            # known DNS resolver in an IP-blocking test). Still reported,
            # not silently dropped, but a distinct category so verdict.py
            # can weight it lower than the same pattern in production code.
            findings.append((
                "suspicious-network-call-test-context", path, line_no,
                f"URL uses a raw IP address (in a test-file path, likely example/fixture data): {text}",
            ))
        else:
            findings.append(("suspicious-network-call", path, line_no, f"URL uses a raw IP address: {text}"))

    if filename in INSTALL_HOOK_PATTERNS:
        for line_no, text in find_matches(content, INSTALL_HOOK_PATTERNS[filename]):
            findings.append(("install-time-script", path, line_no, text))

    return findings


def iter_scan_targets(tree):
    for entry in tree:
        if entry["type"] != "blob":
            continue
        path = entry["path"]
        filename = path.rsplit("/", 1)[-1]
        ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
        if ext in SOURCE_EXTENSIONS or filename in INSTALL_MANIFEST_FILES:
            yield path


def scan(owner, repo):
    print(f"Scanning {owner}/{repo} (code red-flag scan)\n")
    tree = list_tree(owner, repo)
    targets = list(iter_scan_targets(tree))
    total_targets = len(targets)
    if total_targets > MAX_FILES_TO_SCAN:
        print(
            f"  NOTE: {total_targets} candidate files found, capping at "
            f"{MAX_FILES_TO_SCAN} (OI-017 — API-call scaling for very "
            "large repos not yet solved)."
        )
        targets = targets[:MAX_FILES_TO_SCAN]

    print(f"Scanning {len(targets)} of {total_targets} candidate files...\n")

    all_findings = []
    files_scanned = 0
    for path in targets:
        # fetched, scanned, and discarded one at a time -- content never
        # accumulates across files (M4's memory-scaling acceptance criterion)
        try:
            content = fetch_file(owner, repo, path)
        except Exception as e:
            print(f"  Could not fetch {path}: {e}")
            continue
        files_scanned += 1
        all_findings.extend(scan_file_content(path, content))
        del content

    if all_findings:
        print(f"FINDINGS ({len(all_findings)}) across {files_scanned} files scanned:")
        for category, path, line_no, detail in all_findings:
            print(f"  [{category}] {path}:{line_no} — {detail}")
    else:
        print(f"FINDINGS: none across {files_scanned} files scanned.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python code_scan.py <owner/repo>")
        sys.exit(1)
    owner, repo = parse_repo_arg(sys.argv[1])
    scan(owner, repo)


if __name__ == "__main__":
    main()
