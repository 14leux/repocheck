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

from skeleton import fetch_file, parse_repo_arg, strip_invisible_characters

# bumped whenever a pattern list changes (DECISIONS.md #012 -- every
# result should record which ruleset version produced it, since a scan
# repeated a week later can legitimately give a different answer)
RULESET_VERSION = "skill_scan-2026-08-07"

# --- Category 1: red flags -------------------------------------------

SENSITIVE_PATH_PATTERNS = [
    r"~/\.ssh", r"id_rsa", r"id_ed25519", r"\.aws/credentials",
    r"\.aws/config", r"\.npmrc", r"\.pypirc", r"\.netrc",
    r"/etc/passwd", r"\.env\b", r"\.git-credentials",
    r"authorized_keys", r"\.docker/config\.json",
    # found via OI-016: a real example sourced from Snyk's ToxicSkills
    # research (Feb 2026 audit) references a credential-shaped
    # environment variable directly ($ANTHROPIC_API_KEY) rather than a
    # file path -- the original pattern list only looked for files,
    # missing this entire class of ambient-secret-leak instruction.
    r"\$\{?[A-Z_]*(API[_-]?KEY|ACCESS[_-]?KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)[A-Z_]*\}?",
]

EXFIL_VERB_PATTERNS = [
    # found evaded via `curl -d` by independent QA -- curl's short data
    # flag is at least as common as --data/-X POST and wasn't covered
    r"\bcurl\s+.*(-X\s*POST|--data\b|-d\s)",
    r"\brequests\.(post\(|request\(\s*[\"']POST)",
    r"\bfetch\([^)]*\)\s*\.then", r"\bPOST\s+(it|this|them)\s+to\b",
    r"\bupload\s+(it|this|them)\s+to\b", r"\bsend\s+(it|this|them)\s+to\b",
    r"\bexfiltrat",
    # the Snyk-sourced example's exfiltration shape: append a secret to
    # every outgoing request's URL/query/header, an ongoing ambient leak
    # rather than a one-time file-read-then-POST
    r"\b(append|add|include|attach)\b[^\n.]{0,60}\b(as|to)\b[^\n.]{0,40}"
    r"\b(query\s+parameter|url|header|request)\b",
]

INSTRUCTION_OVERRIDE_PATTERNS = [
    r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions?\b",
    r"\bdisregard\s+(the\s+)?system\s+prompt\b",
    # the wildcard is deliberately restricted to not cross a quote
    # character -- found by independent QA: "'you are now' acting
    # instead as a different persona" let the match span across the
    # closing quote to reach an unrelated "instead" that described the
    # quoted phrase rather than being part of it
    r"\byou\s+are\s+now\b[^'\"`]{0,40}\b(instead|not)\b",
    r"\bnew\s+instructions?\s*:",
    r"\bforget\s+everything\b",
    r"\boverride\s+(your|the)\s+(previous\s+)?instructions?\b",
]

# piping into an interpreter is a red flag; piping into a named CLI
# subcommand (e.g. `tool auth login --api-key-stdin`) is not. Also
# catches piping through an intermediary like xargs -- found evaded by
# `curl ... | xargs -0 bash` via independent QA, since the interpreter
# didn't follow the pipe directly.
SHELL_PIPE_EXECUTE_PATTERN = (
    r"\|\s*(sudo\s+)?(xargs\s+(-\d\s+)?)?(bash|sh|zsh|python[23]?|perl|ruby|node|eval)\b"
)

# explicit allowlist for the OI-013 pattern: piping a secret into a
# named CLI's own subcommand is normal, secure practice, not exfiltration.
SAFE_STDIN_PIPE_PATTERN = (
    r"\|\s*[\w.\-]+\s+\S+.*--[\w-]*stdin\b"
)

# found evaded via download-then-execute-on-a-separate-line by
# independent QA (`curl -o p.sh ...` then `bash p.sh` later in the same
# document) -- same class of gap as SHELL_PIPE_EXECUTE_PATTERN but
# without a literal pipe between the two steps. Co-occurrence check
# rather than a single-line regex, same shape as the credential-
# exfiltration check above.
DOWNLOAD_PATTERN = r"\b(curl|wget)\s+[^\n]*-[oO]\s*\S+"
EXECUTE_DOWNLOADED_PATTERN = r"\b(bash|sh|python[23]?|perl|ruby|node)\s+\S+\.(sh|py|pl|rb|js)\b"

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
    content = strip_invisible_characters(content)
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

    # False positive found via M10 dogfooding, then independent QA proved
    # the first fix was overfit: it only recognized ONE exact framing
    # ("asks you to ignore..."). Five newly-written sentences describing
    # the same attack pattern with different wording ("watch for skills
    # that say things like 'ignore previous instructions'", "disregard
    # the system prompt is a classic override phrase used by attackers",
    # etc.) all still misfired. Broadened with two independent signals
    # rather than one narrow phrase list -- still a heuristic, not a
    # complete solution (regex cannot fully distinguish description from
    # performance; this is exactly why DECISION 007's deep-scan pillar
    # exists as a second line of defense for what static matching misses):
    #   1. QUOTED-PHRASE detection: a defensive description overwhelmingly
    #      quotes the example phrase ('ignore previous instructions',
    #      "disregard the system prompt"); a real attack embedded in a
    #      skill is very rarely self-quoted as an example.
    #   2. A wider set of descriptive markers, checked BEFORE and AFTER
    #      the match, not only before.
    DESCRIPTIVE_MARKERS_BEFORE = (
        r"(asks?\s+you\s+to|tries?\s+to|attempts?\s+to|trying\s+to|claims?\s+to|"
        # "might tell the agent:" -- found by independent QA; "the agent"
        # can be followed by ":" (not just "to"), and "might" can precede
        # "tell" with nothing else between them and the marker's end
        r"(might\s+)?tells?\s+the\s+agent(\s+to)?|might\s+tell|say\s+things?\s+like|"
        r"phrasing\s+like|text\s+such\s+as|pattern[s]?\s+(like|such\s+as)|"
        r"watch\s+for|one\s+(pattern|thing)\s+to\s+(detect|watch\s+for)\s+is|"
        r"for\s+example|such\s+as|e\.g\.?|"
        r"if\s+(it|this|anything|the\s+content))\s*[,:]?\s*$"
    )
    DESCRIPTIVE_MARKERS_AFTER = (
        r"^\s*(is\s+a\s+classic|is\s+an\s+example|used\s+by\s+attackers|"
        r"attack\s+pattern|red\s+flag|warning\s+sign|acting\s+instead\s+as|"
        r"appearing\s+(mid-document|in\s+the\s+document))"
    )
    for pat in INSTRUCTION_OVERRIDE_PATTERNS:
        for m in re.finditer(pat, content, re.IGNORECASE):
            preceding = content[max(0, m.start() - 60):m.start()]
            following = content[m.end():m.end() + 60]
            quoted = (
                preceding.rstrip()[-1:] in ("'", '"', "`") if preceding.rstrip() else False
            ) and (
                following.lstrip()[:1] in ("'", '"', "`") if following.lstrip() else False
            )
            descriptive = (
                quoted
                or re.search(DESCRIPTIVE_MARKERS_BEFORE, preceding, re.IGNORECASE)
                or re.search(DESCRIPTIVE_MARKERS_AFTER, following, re.IGNORECASE)
            )
            if descriptive:
                continue  # describing the pattern defensively, not performing it
            line_no = content.count("\n", 0, m.start()) + 1
            text = m.group(0).strip()
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

    download_hits = find_matches(content, [DOWNLOAD_PATTERN])
    execute_hits = find_matches(content, [EXECUTE_DOWNLOADED_PATTERN])
    if download_hits and execute_hits:
        findings.append((
            "shell-pipe-execute",
            f"Content downloads a file ({download_hits[0][1]}) and separately executes "
            f"a script ({execute_hits[0][1]}) -- same risk as piping directly into an "
            "interpreter, split across two steps.",
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
