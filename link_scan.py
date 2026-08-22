#!/usr/bin/env python3
"""
RepoCheck -- README link-integrity scan.

Static regex pass over README markdown links: flags link *text* that
names a well-known trusted domain (ollama.com, lmstudio.ai, github.com
releases, pypi.org, npmjs.com, huggingface.co, ...) whose actual href
resolves somewhere else entirely -- a bait-and-switch pattern neither
the code red-flag scan nor the CVE/freshness pillars have any
mechanism to catch, since the link itself is plain markdown text, not
executable content or a dependency declaration.

Motivating case: unburdened-jackinthebox365/qwen38-uncensored
(found 2026-08-22) -- every link in the README, including ones whose
visible text named ollama.com and lmstudio.ai, actually pointed at the
same self-hosted .zip in the repo's own assets/ folder. The repo's
code/dependency scan came back CLEAR because there was no code to flag
-- the deception lived entirely in the README's link structure.

Separately surfaces README links to binaries/archives hosted directly
in the repo (assets/*.zip, *.exe, *.dmg, *.msi, ...) as a caveat, not a
finding -- hosting your own binary isn't inherently malicious, but an
archive's contents are opaque to a text/code scanner, so a CLEAR
verdict on the repo's visible code says nothing about what's inside
that file. The caveat exists to tell the user what to actually do
about it (see EXPLANATIONS["downloadable-binary-asset"] in verdict.py)
rather than let a CLEAR verdict imply the binary was vetted too.

Hardcoded, no interfaces yet -- same posture as code_scan.py/skill_scan.py
(DECISIONS.md #021).
"""

import re

RULESET_VERSION = "link_scan-2026-08-22"

MARKDOWN_LINK_PATTERN = r"\[([^\]]*)\]\((https?://[^\s)]+)\)"

# badges are near-universal in READMEs, commonly written as
# [![alt](https://img.shields.io/...)](https://real-target.com) -- the
# inner image's own src (the badge-rendering service, e.g. shields.io)
# is not a link a reader can click "to" anything; the outer parens are
# the actual destination. Collapsing image syntax to its alt text
# before parsing links means the outer link is read correctly (text
# from the alt, href from the real target) instead of the inner image
# src being mistaken for where the link goes -- found as a false
# positive against anthropics/anthropic-sdk-python's PyPI badge, which
# otherwise misread the shields.io badge URL as the link's destination.
IMAGE_PATTERN = r"!\[([^\]]*)\]\([^)]*\)"

# domain -> the literal domain string(s) that, if present verbatim in a
# link's visible text while the href resolves elsewhere, indicate the
# text is claiming to go to that domain without actually doing so.
#
# Deliberately restricted to the literal domain string, NOT the bare
# brand/product name -- found as a live false positive scanning
# ollama/ollama's own README, which links to many legitimate
# third-party community tools named after the project (e.g.
# "llm-ollama", "ollama_proxy_server") that point at their own GitHub
# repos, not ollama.com. A bare brand word is an extremely common
# substring in any popular project's own README (full of ecosystem/
# community links naming the project) and produces constant noise;
# the literal domain string (e.g. "ollama.com") is what a bait-and-
# switch link actually needs to display to work as deception, and
# still catches the motivating case (qwen38-uncensored's README used
# "ollama.com" and "lmstudio.ai" verbatim as link labels).
TRUSTED_DOMAIN_MENTIONS = {
    "ollama.com": ["ollama.com"],
    "lmstudio.ai": ["lmstudio.ai"],
    "huggingface.co": ["huggingface.co"],
    "pypi.org": ["pypi.org"],
    "npmjs.com": ["npmjs.com"],
    "github.com": ["github.com"],
    "python.org": ["python.org"],
    "nodejs.org": ["nodejs.org"],
}

BINARY_ASSET_PATTERN = r"\.(zip|exe|dmg|msi|pkg|appimage|deb|rpm)(\?[^)\s]*)?$"


def _domain_of(url):
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1).lower() if m else ""


def scan_readme_links(content):
    """Returns (findings, caveats).

    findings: list of (category, detail) -- link text/href mismatches,
    treated as a real security signal (verdict.py assigns severity).

    caveats: list of (category, detail) -- things flagged but not
    resolvable by static scanning (an in-repo binary this scan cannot
    open and vet), same status as DECISION 020's dynamic-fetch caveat.
    """
    findings = []
    caveats = []
    seen_binary_hrefs = set()

    content = re.sub(IMAGE_PATTERN, lambda m: m.group(1), content)

    for m in re.finditer(MARKDOWN_LINK_PATTERN, content):
        text, href = m.group(1), m.group(2)
        href_domain = _domain_of(href)
        text_lower = text.lower()

        for trusted_domain, mentions in TRUSTED_DOMAIN_MENTIONS.items():
            if trusted_domain == href_domain:
                continue
            if any(mention in text_lower for mention in mentions):
                findings.append((
                    "link-text-domain-mismatch",
                    f"link text mentions '{trusted_domain}' but actually points to "
                    f"'{href_domain}' ({href[:160]})",
                ))
                break  # one finding per link is enough, don't double-report

        if re.search(BINARY_ASSET_PATTERN, href, re.IGNORECASE) and href not in seen_binary_hrefs:
            seen_binary_hrefs.add(href)
            caveats.append((
                "downloadable-binary-asset",
                f"README links to a downloadable archive/executable ({href[:160]}) -- "
                "its contents are opaque to this scan",
            ))

    return findings, caveats
