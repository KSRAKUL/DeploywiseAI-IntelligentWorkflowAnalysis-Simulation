"""Deploywise AI — LLM Provider Abstract Base Class."""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base for all LLM adapters."""

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the LLM completion as a raw string."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and operational."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
