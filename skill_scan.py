#!/usr/bin/env python3
"""
RepoCheck M3 — skill-mode instruction scan.

Static pattern analysis of SKILL.md / skill-manifest prose (DECISIONS.md
#015). Free, default, no LLM call. This is the differentiated pillar —
the dominant attack on Claude Code skills is instruction-shaped, not
code-shaped (CLAUDE.md non-negotiable).

Three pattern categories, kept deliberately separate because they have
very different true/false-positive profiles (DECISIONS.md #020):

1. RED FLAGS — credential-access-plus-exfiltration phrasing,
   instruction-override phrasing, shell-pipe-into-interpreter patterns.
   These are findings.
2. CAVEAT — "fetches and follows external content at runtime." Common in
   entirely legitimate skills (see KNOWLEDGE.md's browser-use trace).
   Never a red flag on its own — reported as an honest,
   unverifiable-by-scanning caveat (DECISIONS.md #020), never folded
   into the same list as red flags.
3. Known-safe patterns are explicitly excluded rather than left to
   accidentally not match — e.g. piping a secret into a named CLI
   subcommand (`... | tool auth login --api-key-stdin`) is NOT a
   shell-pipe-execute red flag; piping into an interpreter
   (`curl ... | bash`) is. This distinction is OI-013's concrete test
   case, found in browser-use's own real skill.

Hardcoded, no interfaces yet — reuses skeleton.py's GitHub access
functions directly rather than through an abstraction (DECISIONS.md
#021: interfaces get extracted at M7, from working code, not designed
in advance).

Usage:
    python skill_scan.py owner/repo path/to/SKILL.md
"""

import re
import sys

from skeleton import fetch_file, parse_repo_arg

# --- Category 1: red flags -------------------------------------------

SENSITIVE_PATH_PATTERNS = [
    r"~/\.ssh", r"id_rsa", r"id_ed25519", r"\.aws/credentials",
    r"\.aws/config", r"\.npmrc", r"\.pypirc", r"\.netrc",
    r"/etc/passwd", r"\.env\b", r"\.git-credentials",
    r"authorized_keys", r"\.docker/config\.json",
]

EXFIL_VERB_PATTERNS = [
    r"\bcurl\s+.*-X\s*POST", r"\bcurl\s+.*--data", r"\brequests\.post\(",
    r"\bfetch\([^)]*\)\s*\.then", r"\bPOST\s+(it|this|them)\s+to\b",
    r"\bupload\s+(it|this|them)\s+to\b", r"\bsend\s+(it|this|them)\s+to\b",
    r"\bexfiltrat",
]

INSTRUCTION_OVERRIDE_PATTERNS = [
    r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions?\b",
    r"\bdisregard\s+(the\s+)?system\s+prompt\b",
    r"\byou\s+are\s+now\b.{0,40}\b(instead|not)\b",
    r"\bnew\s+instructions?\s*:",
    r"\bforget\s+everything\b",
    r"\boverride\s+(your|the)\s+(previous\s+)?instructions?\b",
]

# piping into an interpreter is a red flag; piping into a named CLI
# subcommand (e.g. `tool auth login --api-key-stdin`) is not.
SHELL_PIPE_EXECUTE_PATTERN = (
    r"\|\s*(sudo\s+)?(bash|sh|zsh|python[23]?|perl|ruby|node|eval)\b"
)

# explicit allowlist for the OI-013 pattern: piping a secret into a
# named CLI's own subcommand is normal, secure practice, not exfiltration.
SAFE_STDIN_PIPE_PATTERN = (
    r"\|\s*[\w.\-]+\s+\S+.*--[\w-]*stdin\b"
)

# --- Category 2: caveat, not a red flag -------------------------------

FETCH_AND_FOLLOW_PATTERN = (
    r"\b(read|check|see|fetch|follow|visit)\b[^\n.]{0,60}"
    r"(https?://\S+)"
)


def find_matches(content, patterns):
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, content, re.IGNORECASE):
            line_no = content.count("\n", 0, m.start()) + 1
            hits.append((line_no, m.group(0).strip()))
    return hits


def scan_skill_content(content):
    findings = []
    caveats = []

    # Credential access + exfiltration co-occurrence (weak signal on its
    # own; flagged as a finding requiring review, per OI-013's lesson
    # that naive single-pattern rules misfire).
    sensitive_hits = find_matches(content, SENSITIVE_PATH_PATTERNS)
    exfil_hits = find_matches(content, EXFIL_VERB_PATTERNS)
    if sensitive_hits and exfil_hits:
        findings.append((
            "credential-exfiltration",
            f"Content references sensitive paths ({', '.join(h[1] for h in sensitive_hits)}) "
            f"AND network-send patterns ({', '.join(h[1] for h in exfil_hits)}) "
            "in the same document.",
        ))

    override_hits = find_matches(content, INSTRUCTION_OVERRIDE_PATTERNS)
    for line_no, text in override_hits:
        findings.append((
            "instruction-override",
            f"Line {line_no}: phrasing that tries to override prior instructions — \"{text}\"",
        ))

    # shell-pipe-execute, with the safe-stdin-pipe allowlist checked first
    for m in re.finditer(SHELL_PIPE_EXECUTE_PATTERN, content, re.IGNORECASE):
        line_start = content.rfind("\n", 0, m.start()) + 1
        line_end = content.find("\n", m.end())
        line_end = len(content) if line_end == -1 else line_end
        full_line = content[line_start:line_end].strip()
        if re.search(SAFE_STDIN_PIPE_PATTERN, full_line, re.IGNORECASE):
            continue  # allowlisted: pipe into a named CLI's own subcommand
        line_no = content.count("\n", 0, m.start()) + 1
        findings.append((
            "shell-pipe-execute",
            f"Line {line_no}: pipes content directly into an interpreter — \"{full_line}\"",
        ))

    # fetch-and-follow: caveat category, never a finding
    fetch_hits = find_matches(content, [FETCH_AND_FOLLOW_PATTERN])
    seen_domains = set()
    for line_no, text in fetch_hits:
        url_match = re.search(r"https?://[^\s)\]]+", text)
        if url_match:
            domain = re.match(r"https?://([^/]+)", url_match.group(0)).group(1)
            seen_domains.add(domain)
    if seen_domains:
        caveats.append((
            "dynamic-external-content",
            "This skill instructs the agent to fetch and follow external content "
            f"at runtime from: {', '.join(sorted(seen_domains))}. RepoCheck cannot "
            "verify that content at scan time — it can change after this scan runs. "
            "This is common in legitimate skills and is not itself a red flag; "
            "safety partly depends on trusting these domains to never serve "
            "something different later.",
        ))

    return findings, caveats


def scan(owner, repo, path):
    print(f"Scanning {owner}/{repo}:{path} (skill mode)\n")
    content = fetch_file(owner, repo, path)
    findings, caveats = scan_skill_content(content)

    if findings:
        print(f"FINDINGS ({len(findings)}):")
        for category, detail in findings:
            print(f"  [{category}] {detail}")
    else:
        print("FINDINGS: none")

    print()
    if caveats:
        print(f"CAVEATS ({len(caveats)}) — not findings, informational:")
        for category, detail in caveats:
            print(f"  [{category}] {detail}")
    else:
        print("CAVEATS: none")


def main():
    if len(sys.argv) != 3:
        print("Usage: python skill_scan.py <owner/repo> <path/to/SKILL.md>")
        sys.exit(1)
    owner, repo = parse_repo_arg(sys.argv[1])
    scan(owner, repo, sys.argv[2])


if __name__ == "__main__":
    main()
