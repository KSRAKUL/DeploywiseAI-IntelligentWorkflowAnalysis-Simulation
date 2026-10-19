"""Gemini LLM adapter using Google Gemini REST API."""
from __future__ import annotations

import os
import httpx

from app.config import settings
from app.llm.provider import LLMProvider


class GeminiLLM(LLMProvider):
    """Google Gemini LLM adapter for Deploywise AI advisory agents."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        temperature: float | None = None,
    ) -> None:
        self._api_key = (
            api_key
            or getattr(settings, "gemini_api_key", None)
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or ""
        )
        self._model = model or getattr(settings, "gemini_model", "gemini-1.5-flash")
        self._timeout = timeout or settings.llm_timeout_seconds
        self._temperature = temperature or settings.llm_temperature

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a completion request to Google Gemini API."""
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "temperature": self._temperature,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return "[]"
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return "[]"
            return parts[0].get("text", "[]")

    async def health_check(self) -> bool:
        """Check if Gemini API key is configured and endpoint responds."""
        if not self._api_key:
            return False
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self._api_key}"
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        return f"gemini/{self._model}"
