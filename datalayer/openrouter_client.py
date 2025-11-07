# python
from typing import Optional, List, Dict, Any
import os
import requests


class OpenRouterClient:
    """
    Minimal OpenRouter client wrapper.

    - Reads OPENROUTER_API_KEY from environment.
    - If key is missing, `generate` returns None so callers can use a local fallback.
    - `generate` sends a single-user-message chat completion request and returns
      the assistant text if available.
    """

    def __init__(self, model: str = "gpt-4o-mini", base_url: str = "https://api.openrouter.ai/v1/chat/completions"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = 15

    def _build_payload(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> Optional[str]:
        """
        Return assistant text or None if no API key / call fails.

        Callers should handle None as a signal to use deterministic fallback logic.
        """
        if not self.api_key:
            return None

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = self._build_payload(prompt, max_tokens=max_tokens, temperature=temperature)

        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # On any network / parsing error, return None to allow fallback behavior
            return None

        # Typical response shape: {"choices": [{"message": {"content": "..."}}]}
        try:
            choices = data.get("choices", [])
            if choices and isinstance(choices, list):
                first = choices[0]
                # Support both chat and completion-like shapes
                if isinstance(first.get("message"), dict) and first["message"].get("content"):
                    return first["message"]["content"]
                if first.get("text"):
                    return first["text"]
            # Fallback: try top-level 'output' or other common keys
            for key in ("output", "text"):
                if key in data and isinstance(data[key], str):
                    return data[key]
        except Exception:
            return None

        return None
