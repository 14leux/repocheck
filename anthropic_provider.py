#!/usr/bin/env python3
"""
RepoCheck M9 -- AnthropicModelProvider, the only ModelProvider
implementation in v1 (DECISIONS.md #018).

Raw HTTP via urllib against the Messages API, not the `anthropic` SDK --
keeps the project dependency-free, consistent with every other module
so far (DECISIONS.md #021 was about interface sequencing, not about
avoiding dependencies forever, but there was no reason to add one here).

Reads ANTHROPIC_API_KEY only (DECISIONS.md #014) and fails with a
specific, actionable error if it's unset -- never a generic exception.
"""

import json
import os
import urllib.error
import urllib.request

from interfaces import ModelProvider

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5"


class MissingApiKeyError(RuntimeError):
    pass


class AnthropicModelProvider(ModelProvider):
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model

    def analyze(self, system_prompt, untrusted_content):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise MissingApiKeyError(
                "ANTHROPIC_API_KEY is not set. Deep scan needs your own Anthropic "
                "API key to run (DECISIONS.md #014/#018) -- set it with:\n"
                "  export ANTHROPIC_API_KEY=sk-ant-...\n"
                "Get a key at https://console.anthropic.com/settings/keys. "
                "The free static scan does not need this -- only --deep-scan does."
            )

        body = json.dumps({
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": untrusted_content}],
        }).encode()

        req = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=body,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_API_VERSION,
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise RuntimeError(f"Anthropic API error {e.code}: {detail}") from e

        return "".join(block.get("text", "") for block in data.get("content", []))
