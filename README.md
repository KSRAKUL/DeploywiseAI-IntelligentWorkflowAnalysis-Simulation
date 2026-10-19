# DeploywiseAI-IntelligentWorkflowAnalysis-Simulation

<p align="center">
  <strong>Enterprise Platform for Intelligent Software Workflow Analysis, Deterministic Risk Detection, and What-If Architecture Simulation.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tests-70%20Passed-success?logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

---

## 📖 Table of Contents

- [Overview & Purpose](#-overview--purpose)
- [Key Features](#-key-features)
- [System Architecture & The Golden Rule](#-system-architecture--the-golden-rule)
- [Multi-Modal Project Ingestion](#-multi-modal-project-ingestion)
- [Deterministic Rules Engine (R01–R10)](#-deterministic-rules-engine-r01r10)
- [Human Psychology Scoring Model (100/100 Clean Pass)](#-human-psychology-scoring-model-100100-clean-pass)
- [What-If Risk Simulation & Architecture Diagrams](#-what-if-risk-simulation--architecture-diagrams)
- [Native Security & Reliability Scanners](#-native-security--reliability-scanners)
- [Developer Encouragement & Actionable Guidance](#-developer-encouragement--actionable-guidance)
- [Repository Structure](#-repository-structure)
- [Quick Start Guide](#-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#1-backend-setup)
  - [Frontend Setup](#2-frontend-setup)
  - [Docker Compose Deployment](#3-docker-compose-deployment)
- [Running Automated Tests](#-running-automated-tests)
- [API Reference](#-api-reference)
- [Security, Privacy & Governance](#-security-privacy--governance)
- [License](#-license)

---

## 🎯 Overview & Purpose

Modern software development organizations face severe release risks: broken deployments, missing security scans, unowned production steps, unverified dependency upgrades, and untracked blast radiuses that cause downtime and vulnerabilities.

**Deploywise AI** is an intelligent workflow pre-flight assurance platform. It automatically inspects software delivery pipelines **before execution**, identifies latent risks, computes deterministic policy scores, generates corrected delivery architectures, and allows release teams to test remediation scenarios safely using an in-memory **What-If simulation engine**.

---

## 🌟 Key Features

1. **Deterministic Decisiveness (The Golden Rule)**
   - Pure Python rules (**R01–R10**) and static security scanners calculate risk scores and verdicts without relying on non-deterministic LLM logic.
   - AI models provide advisory summaries and remediation guidance only, ensuring **zero hallucinations in risk scores**.

2. **Human Psychology Delivery Assurance Model (100/100 Clean Pass)**
   - High scores represent superior health: **100/100 indicates a pristine, zero-risk delivery pipeline**.
   - Violations deduct weighted severity penalty points, lowering the score towards 0.
   - Any mandatory blocking violation halts release promotion immediately (`⛔ BLOCKED`).

3. **Multi-Modal Project Ingestion**
   - **GitHub Repositories**: Clones, discovers frameworks, detects CI/CD workflows, and evaluates project structure.
   - **ZIP Archives**: Drag-and-drop code archives with built-in path-traversal protection.
   - **CI/CD Pipelines**: Parses GitHub Actions, GitLab CI, and custom YAML workflow definitions.
   - **Architecture Diagrams & Reports**: OCR and visual pipeline diagram ingestion (PNG, JPEG, SVG, PDF).

4. **Interactive What-If Risk Simulation Console**
   - Speculatively test adding safety gates (Security Scans, Approval Gates, Rollback Plans, Post-Deploy Probes) on in-memory graphs.
   - Instant delta calculation showing baseline score, simulated score, and violation resolution.
   - Side-by-side visualization comparing the **Existing Delivery Pipeline** with the **Future Delivery Pipeline (Proposed Target State)**.
   - **Original workflows are strictly immutable and never mutated**.

5. **Native Security Scanners**
   - Built-in static secret detection (AWS keys, GitHub tokens, generic private keys, credentials).
   - Dockerfile hygiene scanner (root execution, latest tags, credential exposure).
   - Dependency vulnerability and lockfile verification.

6. **Executive PDF & Markdown Reports**
   - Audit-ready, exportable reports including execution coverage, category breakdown, remediation roadmaps, and policy versions.

---

## 🏛 System Architecture & The Golden Rule

```
                      ┌──────────────────────────────────────────────┐
                      │          MULTI-MODAL INGESTION LAYER         │
                      │  GitHub Repo | ZIP Upload | CI/CD | Diagram  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          PROJECT DISCOVERY ENGINE            │
                      │  Stack Detection | File Parser | Topo-Sort   │
                      └──────────────────────┬───────────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     │                                               │
                     ▼                                               ▼
      ┌─────────────────────────────┐                 ┌─────────────────────────────┐
      │  DETERMINISTIC ENGINE (R-R) │                 │   NATIVE STATIC SCANNERS    │
      │  Rules R01 - R10 Evaluation │                 │  Secrets | Docker | Package │
      └──────────────┬──────────────┘                 └──────────────┬──────────────┘
                     │                                               │
                     └───────────────────────┬───────────────────────┘
                                             │ Verified Findings
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          FROZEN SCORING ENGINE               │
                      │  Weighted Category Sum (Banker's Rounding)   │
                      │  Assurance Score = 100 - Penalty Deductions  │
                      └──────────────────────┬───────────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     │                                               │
                     ▼ (Deterministic)                               ▼ (Strictly Advisory)
      ┌─────────────────────────────┐                 ┌─────────────────────────────┐
      │   VERDICT & BLOCKING GATE   │                 │   AI ADVISORY REVIEWERS     │
      │   PASS | REVIEW | BLOCKED   │                 │   Gemini 1.5 Flash / Ollama │
      │   (Zero LLM Hallucinations) │                 │   (Explains & Guides Only)  │
      └──────────────┬──────────────┘                 └──────────────┬──────────────┘
                     │                                               │
                     └───────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    ENTERPRISE WEB CONSOLE & WHAT-IF ENGINE   │
                      │  Existing vs Future Diagrams | PDF Reports   │
                      └──────────────────────────────────────────────┘
```

### The Golden Rule
> **Deterministic Decisiveness:**
> Risk scores, category weights, and release-blocking verdicts are decided **exclusively** by deterministic Python rules and static scanners. AI models act as specialist advisors (`source="agent"`, `advisory=True`, `blocking=False`) and can never alter numeric scores, severity ratings, or release verdicts.

---

## 📥 Multi-Modal Project Ingestion

Deploywise AI accepts input through 4 primary ingestion channels:

1. **GitHub Repository URL**:
   - Clones repository directly into isolated temporary storage.
   - Automatically detects languages (Python, TypeScript, Go, Java, Rust, Docker, etc.), frameworks, and package manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`).
   - Identifies CI/CD pipelines under `.github/workflows/` and `.gitlab-ci.yml`.

2. **ZIP Archive Upload**:
   - Secure extraction engine with **Zip-Slip protection** preventing path traversal attacks.
   - Extracts, catalogs, and analyzes directory trees up to 50 MB.

3. **CI/CD Pipeline Content (YAML)**:
   - Paste GitHub Actions or workflow definitions directly.
   - Reconstructs pipeline stage DAGs, execution dependencies, and environment targets.

4. **Architecture Diagrams & Project Reports (PNG / JPEG / SVG / PDF)**:
   - Uses OCR and multi-modal vision intelligence to interpret visual workflows and system architecture blueprints.
   - Reconstructs declared stages and outputs interactive Mermaid DAGs.

---

## 📋 Deterministic Rules Engine (R01–R10)

All 10 core safety rules are deterministically evaluated against the workflow Directed Acyclic Graph (DAG):

| Rule ID | Rule Name | Category | Default Severity | Blocking | Detection Logic |
|:---:|:---|:---:|:---:|:---:|:---|
| **R01** | Missing Automated Tests | Testing | High | No | Triggered when deployment to production occurs without a prior `unit_test` or `integration_test` stage. |
| **R02** | Missing Security Scan | Security | Critical | **Yes (BLOCKED)** | Triggered when a production deployment workflow lacks an automated vulnerability or secrets security scan. |
| **R03** | Missing Governance Approval | Governance | Critical | **Yes (BLOCKED)** | Triggered when changes target production without an explicit human approval or release governance gate. |
| **R04** | No Rollback Plan | Recovery | High / Critical | No | Triggered when a production deployment has no automated rollback procedure. Escalates to **Critical** on high blast radius. |
| **R05** | Unowned Stage | Governance | Medium / High | No | Triggered when any pipeline stage lacks a designated responsible owner or team email. Escalates to **High** on production stages. |
| **R06** | Invalid Gate Ordering | Dependency | High | No | Triggered when an approval or validation gate is topologically positioned after the production deployment stage. |
| **R07** | Missing Post-Deploy Probe | Recovery | Medium | No | Triggered when a production deployment has no post-deploy health check or canary monitoring verification. |
| **R08** | Unverified Dependency Change | Dependency | High | No | Triggered when project dependencies have changed (`dependencies_changed=true`) but no dependency audit stage ran. |
| **R09** | Bypassable Safety Gates | Testing | High | No | Triggered when test or validation stages have `continue_on_failure: true` or skippable execution flags enabled. |
| **R10** | Missing Staging Validation | Testing | Medium | No | Triggered when promotion to production lacks a staging environment validation and smoke-testing phase. |

---

## 📊 Human Psychology Scoring Model (100/100 Clean Pass)

Deploywise AI adopts the **human psychology scoring standard**:
- **100 / 100** represents a pristine, completely clean pipeline.
- Identified violations deduct weighted severity penalty points.
- **Delivery Assurance Score** is calculated as:

$$\text{Delivery Assurance Score} = \max\left(0, \min\left(100, 100 - \sum_{\text{categories}} (\text{Capped Category Penalty} \times \text{Weight})\right)\right)$$

### Category Weights (Sum = 100%)
- **Security**: 25% (0.25)
- **Testing**: 25% (0.25)
- **Recovery**: 20% (0.20)
- **Dependency**: 15% (0.15)
- **Governance**: 15% (0.15)
- **Category Cap**: 100 points maximum penalty per category.

### Severity Penalty Points (Subtracted from 100)
- **Critical**: -50 points
- **High**: -30 points
- **Medium**: -15 points
- **Low**: -5 points

### Verdict Thresholds
| Assurance Score | Verdict | Status & Meaning |
|:---:|:---:|:---|
| **100 / 100** | **100% CLEAN PASS** | Zero violations; pristine, fully-guarded workflow. |
| **≥ 70 / 100** | **PASS** | Deductions < 30 points; safe for production release. |
| **40 – 69 / 100** | **NEEDS_REVIEW** | Deductions 30–59 points; non-critical checks failed. Review recommended. |
| **< 40 / 100** | **HIGH_RISK** | Deductions ≥ 60 points; elevated delivery risk detected across controls. |
| **Any Blocker** | **BLOCKED** | Mandatory safety gate violation (**R02**, **R03**, or critical blocker). Immediate release block. |

---

## 🔬 What-If Risk Simulation & Architecture Diagrams

The **What-If Simulation Console** allows engineers and release managers to test graph changes in memory:
- **1-Click Remediation**: Add security scans, governance gates, rollback stages, or post-deploy health probes with single-click presets.
- **Custom Operations**: Add or remove arbitrary nodes and rewire dependencies.
- **Instant Risk Delta**: Compares baseline vs. simulated scores and tracks whether the verdict upgrades from `BLOCKED` to `PASS`.
- **Side-by-Side Mermaid Diagrams**:
  - **Existing Delivery Pipeline**: Highlights detected vulnerabilities and missing gates in red.
  - **Future Delivery Pipeline (Proposed Target State)**: Visualizes the remediated workflow with added safety gates in blue/green.

---

## 🛡 Native Security & Reliability Scanners

Deploywise AI includes native, self-contained static analysis engines that require no external SaaS subscriptions:

1. **Native Secret Scanner**:
   - Detects AWS Access Keys (`AKIA...`), GitHub Personal Access Tokens (`ghp_...`), Google API Keys (`AIzaSy...`), Slack tokens, generic private keys, and hardcoded passwords.
2. **Native Dockerfile Hygiene Scanner**:
   - Flags missing non-root user declarations (`USER`), unpinned base images (`:latest`), exposed sensitive ports, and missing healthcheck instructions (`HEALTHCHECK`).
3. **Native Dependency & Lockfile Scanner**:
   - Audits manifests across npm (`package.json`), Python (`requirements.txt`, `Pipfile`), and Go (`go.mod`).

---

## 💡 Developer Encouragement & Actionable Guidance

Rather than just listing errors, Deploywise AI motivates engineers through positive feedback and actionable guidance:
- **Status Levels**: `healthy`, `needs_attention`, `blocked`, `verified`, `partial_evidence`.
- **Targeted Action Item**: Every finding includes **Evidence Detected**, **Why It Matters**, **Potential Consequence**, **Recommended Fix**, and **Verification Criteria**.
- **1-Click Copy Fix**: Copy ready-to-apply patches for GitHub Actions, Dockerfiles, and configuration files.

---

## 📁 Repository Structure

```
DeploywiseAI/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints (assessments, workflows, reports, audit, health)
│   │   ├── core/            # Core deterministic engine
│   │   │   ├── rules/       # R01–R10 deterministic rule implementations
│   │   │   ├── graph.py     # NetworkX DAG reachability & cycle detection
│   │   │   ├── scoring.py   # Frozen scoring engine & banker's rounding
│   │   │   ├── schemas.py   # Pydantic v2 data contracts
│   │   │   └── policy.py    # Policy configuration loader
│   │   ├── db/              # SQLAlchemy async database models & sessions
│   │   ├── ingestion/       # GitHub repo, ZIP, CI/CD, and diagram parsers
│   │   ├── scanners/        # Native secret, docker, and dependency scanners
│   │   ├── services/        # Orchestration, diagrams, what-if, encouragement
│   │   ├── reporting/       # PDF & Markdown report generators
│   │   ├── llm/             # Bounded LLM adapters (Gemini, Ollama, Fake)
│   │   ├── config.py        # Pydantic Settings configuration
│   │   └── main.py          # FastAPI application entry point
│   ├── tests/               # 70 passing unit, integration, and scoring tests
│   ├── pyproject.toml       # Backend dependencies & metadata
│   ├── Dockerfile           # Backend container build
│   └── .env.example         # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/      # AppShell, RiskScoreGauge, MermaidViewer, FindingDrawer
│   │   ├── views/           # ProjectAssessment, Workflows, WhatIf, Analysis, Reports, Settings
│   │   ├── lib/api.ts       # Typed REST API client
│   │   ├── types/index.ts   # Shared TypeScript interface definitions
│   │   ├── App.tsx          # Root view routing & sample workflows
│   │   └── main.tsx         # React DOM entry point
│   ├── package.json         # Frontend dependencies (React, Vite, Lucide, Mermaid)
│   ├── tsconfig.json        # TypeScript strict configuration
│   ├── vite.config.ts       # Vite bundler & dev server config
│   └── Dockerfile           # Frontend container build
├── data/
│   ├── policies/            # default_policy_v1.yaml (Frozen policy weights)
│   └── sample_workflows/    # 6 pre-configured evaluation scenarios
├── docs/
│   ├── ARCHITECTURE.md      # Detailed system architecture & design
│   ├── DECISIONS.md         # Architecture Decision Records (ADRs)
│   ├── DEMO_SCRIPT.md       # Interactive evaluation walkthrough guide
│   └── Deploywise_AI_Project_Blueprint.md
├── docker-compose.yml       # Production multi-container orchestration
├── .gitignore               # Strict exclusion of secrets, DBs, and artifacts
├── .env.example             # Root environment template
└── README.md                # Comprehensive documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher (npm 9+)
- **Git**

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -e .

# Copy environment configuration
cp .env.example .env

# Start FastAPI development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

- **Web Application Console**: [http://localhost:3000](http://localhost:3000)

---

### 3. Docker Compose Deployment

Run the complete multi-tier application with a single command:

```bash
docker-compose up --build
```

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`

---

## 🧪 Running Automated Tests

Deploywise AI includes a test suite covering unit tests, frozen scoring regression tests, static scanner validation, and API integration:

```bash
cd backend
pytest -v
```

```text
============================== test session starts ==============================
collected 70 items

tests/test_api.py::test_health_check_endpoint PASSED                     [  1%]
tests/test_api.py::test_create_workflow_valid PASSED                     [  2%]
tests/test_api.py::test_what_if_simulation_never_mutates_workflow PASSED [ 10%]
tests/test_assessments.py::test_native_secret_scanner PASSED             [ 18%]
tests/test_assessments.py::test_native_dependency_scanner PASSED         [ 20%]
tests/test_assessments.py::test_native_docker_scanner PASSED             [ 21%]
tests/test_assessments.py::test_pdf_report_generation PASSED             [ 22%]
tests/test_rules.py::test_registry_has_10_rules PASSED                   [ 34%]
tests/test_scoring.py::test_canonical_regression_score PASSED            [ 84%]
tests/test_validators.py::test_graph_detects_cyclic_dependency PASSED    [ 94%]
...
====================== 70 passed, 0 failed in 19.5s =============================
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|:---:|:---|:---|
| `GET` | `/health` | Returns service status, active LLM provider, and scanner readiness. |
| `POST` | `/assessments/github` | Clones and inspects any GitHub repository URL. |
| `POST` | `/assessments/zip` | Ingests an uploaded project ZIP archive safely. |
| `POST` | `/assessments/cicd` | Analyzes CI/CD pipeline YAML content. |
| `POST` | `/assessments/diagram` | Ingests an architecture image (PNG, SVG, JPEG) or PDF design doc. |
| `GET` | `/assessments` | Lists recent assessments with summary metrics. |
| `GET` | `/assessments/{id}` | Fetches full assessment details, findings, diagrams, and roadmap. |
| `GET` | `/assessments/{id}/pdf` | Downloads the executive PDF assurance report. |
| `POST` | `/workflows` | Creates a new workflow definition. |
| `GET` | `/workflows` | Lists persisted workflow definitions. |
| `POST` | `/workflows/{id}/analyze` | Executes deterministic analysis and stores results. |
| `POST` | `/workflows/{id}/what-if` | Runs in-memory speculative simulation with proposed changes. |
| `GET` | `/reports/{analysis_id}` | Exports report in JSON or Markdown format. |
| `POST` | `/audit/decisions` | Records a human reviewer governance sign-off into the audit log. |
| `GET` | `/audit` | Retrieves the immutable append-only governance audit trail. |
| `GET` | `/policy` | Returns frozen category weights, penalty points, and thresholds. |

---

## 🔒 Security, Privacy & Governance

- **Zero Secret Exposure**: `.env` files, credentials, and API keys are strictly excluded via `.gitignore`.
- **Zip-Slip Safe Extraction**: Archives are validated against path traversal before extraction.
- **Append-Only Audit Trail**: Every analysis and human review decision is recorded with timestamps, actor IDs, and immutable snapshots.
- **Isolated LLM Execution**: Even when configured with cloud models like Gemini, LLM failures or timeouts will never compromise deterministic scoring or fail pipeline evaluations.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
