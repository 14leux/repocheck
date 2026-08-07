#!/usr/bin/env python3
"""
RepoCheck M7 -- GitHub implementation of FileAccessProvider.

The only file-access implementation in v1 (DECISIONS.md #012). Moved
here verbatim from skeleton.py's original github_get/list_tree/
fetch_file functions -- an extraction, not a rewrite.
"""

import base64
import io
import json
import os
import tarfile
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

    def fetch_all_files(self, owner, repo, paths):
        """
        OI-017 fix: one tarball download instead of one contents-API
        call per file. GitHub's tarball endpoint redirects to
        codeload.github.com, which urllib follows automatically; no
        auth token needed for a public repo's tarball (this is the
        scanning use case -- vetting a public repo before trusting it).

        Falls back to the inherited per-file default if the tarball
        download fails for any reason (private repo needing auth this
        path doesn't send, network issue, etc.) -- a slower scan, never
        a crashed one.
        """
        wanted = set(paths)
        try:
            info = self._get(f"/repos/{owner}/{repo}")
            branch = info["default_branch"]
            url = f"{GITHUB_API}/repos/{owner}/{repo}/tarball/{branch}"
            req = urllib.request.Request(url, headers={"User-Agent": "repocheck-skeleton"})
            with urllib.request.urlopen(req) as resp:
                archive_bytes = resp.read()
        except Exception:
            return super().fetch_all_files(owner, repo, paths)

        result = {}
        found = set()
        try:
            with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    # tarball members are prefixed "{owner}-{repo}-{sha}/"
                    parts = member.name.split("/", 1)
                    if len(parts) != 2:
                        continue
                    rel_path = parts[1]
                    if rel_path in wanted:
                        f = tar.extractfile(member)
                        if f is not None:
                            result[rel_path] = f.read().decode("utf-8", errors="replace")
                            found.add(rel_path)
        except tarfile.TarError:
            return super().fetch_all_files(owner, repo, paths)

        for path in wanted - found:
            result[path] = FileNotFoundError(f"{path} not found in tarball")
        return result
