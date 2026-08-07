#!/usr/bin/env python3
"""
RepoCheck M7 -- pluggable interfaces, extracted from M2-M6's working
code rather than designed in advance (DECISIONS.md #021).

FileAccessProvider is a real extraction: every one of skeleton.py,
skill_scan.py, code_scan.py, freshness_scan.py, and verdict.py already
depended on exactly two operations (list a repo's file tree, fetch one
file's content) via skeleton.py's module-level `list_tree`/`fetch_file`.
That existing chokepoint is what made this extraction cheap -- GitHub is
the only implementation shipped (DECISIONS.md #012), but the interface
now exists so a GitLab/Bitbucket implementation can be added later
without touching any calling code.

ModelProvider is forward-defined, not extracted -- M9 (opt-in deep
scan) hasn't been built yet, so there is no working code to extract it
from. Defined now so M9 can be written directly against the interface
(DECISIONS.md #018), but its "swap and prove nothing breaks" claim
can't be demonstrated the same way FileAccessProvider's can until M9
exists to call it.
"""

from abc import ABC, abstractmethod


class FileAccessProvider(ABC):
    @abstractmethod
    def list_tree(self, owner, repo):
        """Return a list of {"path": str, "type": "blob"|"tree", ...} entries
        for the repo's default branch, recursive."""
        raise NotImplementedError

    @abstractmethod
    def fetch_file(self, owner, repo, path):
        """Return the raw text content of one file."""
        raise NotImplementedError


class ModelProvider(ABC):
    @abstractmethod
    def analyze(self, system_prompt, untrusted_content):
        """
        Run the deep-scan reasoning pass. `untrusted_content` must be
        structurally delimited by the caller so it is never interpreted
        as instructions (DECISIONS.md #016, non-negotiable) -- this
        method's job is to call the model, not to enforce that
        delimiting itself.
        """
        raise NotImplementedError
