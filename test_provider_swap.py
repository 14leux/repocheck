#!/usr/bin/env python3
"""
RepoCheck M7 -- demonstrates the acceptance criterion "adding a second
implementation of [FileAccessProvider] requires no change to calling
code," with a stub, not just asserted.

FakeFileAccessProvider serves canned data with zero network calls.
Swapping it in via skeleton.swap_provider() and then calling
find_manifests() (skeleton.py) and scan_file_content() (code_scan.py)
proves the swap works through the whole call chain without touching
either of those files.
"""

import skeleton
from code_scan import scan_file_content
from interfaces import FileAccessProvider


class FakeFileAccessProvider(FileAccessProvider):
    """Serves a canned in-memory repo: one pyproject.toml with a
    dependency, and one Python file with an obvious red flag -- enough
    to prove both the manifest-parsing and code-scan paths still work
    end to end against a non-GitHub provider."""

    def __init__(self):
        self.files = {
            "pyproject.toml": (
                '[project]\n'
                'dependencies = ["requests==2.0.0"]\n'
            ),
            "payload.py": (
                "import base64\n"
                "exec(base64.b64decode(b'malicious'))\n"
            ),
        }

    def list_tree(self, owner, repo):
        return [{"path": path, "type": "blob"} for path in self.files]

    def fetch_file(self, owner, repo, path):
        return self.files[path]


def main():
    skeleton.swap_provider(FakeFileAccessProvider())

    # skeleton.py's own logic, untouched, now reading from the fake provider
    tree = skeleton.list_tree("fake", "fake")
    manifests = skeleton.find_manifests(tree)
    assert manifests == [("pyproject.toml", "PyPI")], manifests
    content = skeleton.fetch_file("fake", "fake", "pyproject.toml")
    deps = skeleton.PARSERS["pyproject.toml"](content)
    assert deps == [("requests", "2.0.0")], deps
    print("skeleton.py: find_manifests + fetch_file + parser all worked against the fake provider")

    # code_scan.py's own logic, untouched, now reading from the fake provider
    payload_content = skeleton.fetch_file("fake", "fake", "payload.py")
    findings = scan_file_content("payload.py", payload_content)
    assert any(f[0] == "obfuscation" for f in findings), findings
    print("code_scan.py: scan_file_content caught the obfuscation finding via the fake provider")

    print("\nPASS -- FileAccessProvider swap required zero changes to skeleton.py or code_scan.py")


if __name__ == "__main__":
    main()
