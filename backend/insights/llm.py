from __future__ import annotations

import json
import os
from typing import Any

import requests


class LocalLLMError(RuntimeError):
    pass


class LocalLLMClient:
    def __init__(self):
        self.provider = os.getenv("LOCAL_LLM_PROVIDER", "ollama").lower()
        self.model = os.getenv("LOCAL_LLM_MODEL", "llama3.1:8b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.lmstudio_url = os.getenv("LMSTUDIO_URL", "http://localhost:1234")
        self.timeout_seconds = int(os.getenv("LOCAL_LLM_TIMEOUT_SECONDS", "45"))

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if self.provider == "lmstudio":
            content = self._generate_lmstudio(prompt)
        else:
            content = self._generate_ollama(prompt)

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LocalLLMError(f"Model did not return valid JSON: {exc}") from exc

    def generate_text(self, prompt: str) -> str:
        if self.provider == "lmstudio":
            return self._generate_lmstudio(prompt)
        return self._generate_ollama(prompt)

    def _generate_ollama(self, prompt: str) -> str:
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0, "num_predict": 220},
            },
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise LocalLLMError("Ollama request failed")
        payload = response.json()
        return (payload.get("response") or "").strip()

    def _generate_lmstudio(self, prompt: str) -> str:
        response = requests.post(
            f"{self.lmstudio_url}/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 260,
            },
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise LocalLLMError("LM Studio request failed")
        payload = response.json()
        return (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
