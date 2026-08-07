#!/usr/bin/env python3
"""
RepoCheck M7 -- GitHub implementation of FileAccessProvider.

The only file-access implementation in v1 (DECISIONS.md #012). Moved
here verbatim from skeleton.py's original github_get/list_tree/
fetch_file functions -- an extraction, not a rewrite.
"""

import base64
import json
import os
import urllib.error
import urllib.request

from interfaces import FileAccessProvider

GITHUB_API = "https://api.github.com"


class GitHubFileAccessProvider(FileAccessProvider):
    def _get(self, path):
        url = GITHUB_API + path
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "repocheck-skeleton",
            },
        )
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"GitHub API error for {path}: {e.code} {e.reason}") from e

    def list_tree(self, owner, repo):
        info = self._get(f"/repos/{owner}/{repo}")
        branch = info["default_branch"]
        tree = self._get(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        if tree.get("truncated"):
            print(
                "  WARNING: repo tree was truncated by GitHub's API -- "
                "this repo is too large for a single recursive listing. "
                "Some manifests may be missed."
            )
        return tree.get("tree", [])

    def fetch_file(self, owner, repo, path):
        data = self._get(f"/repos/{owner}/{repo}/contents/{path}")
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
