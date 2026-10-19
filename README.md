# DeploywiseAI-IntelligentWorkflowAnalysis-Simulation

> **Deploywise AI** — Enterprise Platform for Intelligent Software Workflow Analysis, Deterministic Risk Detection, and What-If Architecture Simulation.

Deploywise AI reviews software delivery pipelines before execution, detects missing security and reliability controls, explains their risk impact, and lets reviewers simulate safer architectures through **What-If** analysis before recording human governance decisions.

---

## 🌟 Key Features

1. **Deterministic Decisiveness (The Golden Rule):**
   - Pure Python rules (R01–R10) alone compute risk scores, category penalties, and blocking verdicts.
   - Bounded AI specialist reviewers (QA, Security, Operations, Dependency) provide labelled advisory observations only.
   - **Zero AI Hallucination in Risk Scores:** No AI model can change scores, severity, or blocking verdicts.

2. **Transparent Policy-Driven Scoring (100/100 Clean Pass Model):**
   - Frozen category weights: Security (25%), Testing (25%), Recovery (20%), Dependency (15%), Governance (15%).
   - Capped at 100 points per category with banker's rounding (`round()`).
   - High assurance score: 100/100 represents a clean, fully passed pipeline; violations deduct penalty points.
   - Any blocking violation triggers `⛔ BLOCKED`.

3. **In-Memory What-If Simulation:**
   - Test proposed additions (e.g. adding security scans, approval gates, or rollback plans) on cloned graphs.
   - Live before/after risk score diff, verdict upgrade tracking, and violation resolution analysis.
   - Side-by-side **Existing Delivery Pipeline** vs **Future Delivery Pipeline (Proposed Target State)** Mermaid architecture diagrams.
   - Original workflows are **never mutated**.

4. **Multi-Modal Project Ingestion:**
   - **GitHub Repositories:** Clone and inspect any public or authenticated GitHub repository URL.
   - **ZIP Archives:** Direct drag-and-drop project upload with zip slip protection.
   - **CI/CD Pipelines:** GitHub Actions, GitLab CI, and YAML workflow ingestion.
   - **Visual Diagrams:** Vision intelligence for PNG, JPEG, SVG, and PDF workflow architectures.

5. **Multi-Provider AI Reviewers:**
   - **FakeLLM:** Guaranteed zero-network testing for CI/CD.
   - **Ollama:** Local offline inference.
   - **Google Gemini:** Cloud inference powered by Gemini 1.5 Flash via `GEMINI_API_KEY`.

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
pip install -e .
python -m uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Console: `http://localhost:3000`

### 3. Run Test Suite
```bash
cd backend
python -m pytest -v
```
All 70 unit, validator, scoring regression, scanner, diagram, and API integration tests will run and pass.

---

## 📋 Deterministic Rules (R01–R10)

| Rule ID | Rule Name | Category | Default Severity | Blocking |
|---|---|---|---|---|
| **R01** | Missing Tests | Testing | High | No |
| **R02** | Missing Security Scan | Security | Critical | **Yes** |
| **R03** | Missing Approval Gate | Governance | Critical | **Yes** |
| **R04** | No Rollback Plan | Recovery | High / Critical | No |
| **R05** | Unowned Stage | Governance | Medium / High | No |
| **R06** | Invalid Stage Order | Dependency | High | No |
| **R07** | Missing Monitoring Check | Recovery | Medium | No |
| **R08** | Unverified Dependency Change | Dependency | High | No |
| **R09** | Tests Bypassable / Skippable | Testing | High | No |
| **R10** | No Staging Validation | Testing | Medium | No |

---

## 📁 Repository Structure

```
deploywise-ai/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI transport endpoints (health, workflows, reports, audit)
│   │   ├── core/
│   │   │   ├── rules/       # R01-R10 deterministic rule implementations
│   │   │   ├── graph.py     # NetworkX DAG reachability analysis
│   │   │   ├── scoring.py   # Deterministic scoring algorithm
│   │   │   ├── schemas.py   # Frozen Pydantic v2 data contracts
│   │   │   └── policy.py    # Policy configuration loader
│   │   ├── agents/          # Advisory specialist reviewers & validator
│   │   ├── llm/             # FakeLLM, Ollama, and Google Gemini adapters
│   │   └── services/        # Analysis pipeline & What-If simulation
│   └── tests/               # 57 passing unit & integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # AppShell, GraphCanvas, RiskScoreGauge, FindingDrawer
│   │   ├── views/           # Overview, Workflows, Builder, Analysis, What-If, Reports, Audit, Settings
│   │   ├── lib/api.ts       # Typed API client
│   │   └── index.css        # Enterprise operations light-theme CSS tokens
├── data/
│   ├── policies/            # default_policy_v1.yaml
│   └── sample_workflows/    # 6 pre-configured test scenarios
└── docs/
    ├── ARCHITECTURE.md      # System architecture & mermaid diagrams
    ├── DECISIONS.md         # Architecture decision log
    └── DEMO_SCRIPT.md       # Step-by-step manager walkthrough
```
