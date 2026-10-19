"""
Deploywise AI — LLM Factory.
Returns the configured LLM provider based on settings.
"""
from __future__ import annotations

from app.config import settings
from app.llm.provider import LLMProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance."""
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        from app.llm.gemini import GeminiLLM
        return GeminiLLM()
    elif provider == "ollama":
        from app.llm.ollama import OllamaLLM
        return OllamaLLM()
    else:
        from app.llm.fake import FakeLLM
        return FakeLLM()
