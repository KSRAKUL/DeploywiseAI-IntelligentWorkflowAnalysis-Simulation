# Deploywise AI — Architectural Decisions Log (DECISIONS.md)

## Decision 001: Golden Rule — Deterministic Decisiveness & Bounded Advisory AI
- **Status:** ACCEPTED
- **Date:** 2026-10-12
- **Context:** AI models can hallucinate, suffer from non-deterministic variance, or be manipulated via adversarial inputs. In CI/CD and release governance, decisions must be predictable, auditable, and repeatable.
- **Decision:** Pure Python deterministic rules (R01–R10) alone compute risk scores, category scores, and blocking verdicts. Specialist AI agents (Security, QA, Operations, Dependency, Recommendation) are strictly advisory (`source="agent"`, `advisory=True`, `blocking=False`).
- **Consequences:** Even if an LLM is unreachable or outputs malformed text, the deterministic analysis pipeline runs and delivers accurate risk scores and verdicts without interruption.

---

## Decision 002: Frozen Data Contracts & Banker's Rounding
- **Status:** ACCEPTED
- **Date:** 2026-10-12
- **Context:** Schemas and scoring weights must be permanently stable across all release versions.
- **Decision:**
  - `backend/app/core/schemas.py` is frozen (tagged `contracts-v1`).
  - `data/policies/default_policy_v1.yaml` weights and penalty points are frozen.
  - Python's built-in `round()` (round half to even / banker's rounding) is frozen for computing integer scores from weighted category sums.
  - Canonical regression test (`0.25*50 + 0.25*15 + 0.20*65 + 0.15*0 + 0.15*80 = 41.25 -> 41`) must pass permanently.

---

## Decision 003: Speculative-Only What-If Simulation Semantics
- **Status:** ACCEPTED
- **Date:** 2026-10-12
- **Context:** Reviewers need to experiment with adding missing security scans or approval gates without mutating the saved production workflow definition.
- **Decision:** `POST /workflows/{id}/what-if` operates exclusively on in-memory clones of the workflow graph. Saved records in SQLite/PostgreSQL are never mutated. Saving a proposed simulation requires an explicit separate user action.

---

## Decision 004: Multi-Provider LLM Architecture (FakeLLM / Ollama / Gemini)
- **Status:** ACCEPTED
- **Date:** 2026-10-12
- **Context:** The system needs zero-network determinism for unit and regression tests, local offline privacy via Ollama, and high-capability cloud inference via Google Gemini 1.5 Flash when the user provides an API key.
- **Decision:** An abstract `LLMProvider` interface supports:
  - `FakeLLM`: Returns controlled, schema-conforming advisory findings for offline tests.
  - `OllamaLLM`: Local model invocation via HTTP (`http://localhost:11434/api/chat`).
  - `GeminiLLM`: Google Gemini 1.5 Flash support via Google Generative Language REST API (`GEMINI_API_KEY` / `GOOGLE_API_KEY`).
