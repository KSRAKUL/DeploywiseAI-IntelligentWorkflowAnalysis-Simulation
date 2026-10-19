"""Ollama LLM adapter."""
from __future__ import annotations

import httpx

from app.config import settings
from app.llm.provider import LLMProvider


class OllamaLLM(LLMProvider):
    """Ollama local model adapter."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        temperature: float | None = None,
    ) -> None:
        self._model = model or settings.ollama_model
        self._base_url = base_url or settings.ollama_base_url
        self._timeout = timeout or settings.llm_timeout_seconds
        self._temperature = temperature or settings.llm_temperature

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request to Ollama."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": self._temperature},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def health_check(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        return f"ollama/{self._model}"
