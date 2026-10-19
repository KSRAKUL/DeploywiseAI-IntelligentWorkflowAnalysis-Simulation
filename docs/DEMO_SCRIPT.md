# Deploywise AI — Manager Demonstration Walkthrough (DEMO_SCRIPT.md)

Use this script to demonstrate Deploywise AI's core capabilities, the Golden Rule, and What-If simulation.

---

### Step 1: Health & Offline Determinism Verification
1. Start the backend: `python -m uvicorn app.main:app --port 8000`
2. Start the frontend: `npm run dev`
3. Open `http://localhost:3000` in your browser.
4. Verify the top header shows: `Deterministic Core: Active` and `DEMO` environment badge.
5. In **Policy & Settings**, observe that LLM provider defaults to `fake` (or Ollama/Gemini), and the scoring rules run with 100% reliability offline without external API dependencies.

---

### Step 2: Ingest Risky Pipeline (`01_bad_release.json`)
1. On the **Overview** page, click the quick preset button: **`01 Bad Release (Missing Gates)`**.
2. Notice the system automatically uploads and analyzes the pipeline:
   - **Score:** High risk / blocked score.
   - **Verdict:** `⛔ BLOCKED`.
   - **Reason:** Blocking rule violations `[R02] No security scan before production deploy` and `[R03] No approval gate before production deploy`.
   - **Unowned deploy:** `[R05] Unowned stage: 'Deploy to Production'`.

---

### Step 3: Inspect Finding Detail Drawer
1. In the Risk Findings list, click on `[R02] No security scan before production deploy`.
2. Observe the drawer sliding out displaying:
   - **Exact Evidence:** Affected stage IDs and path analysis.
   - **Why It Matters:** Vulnerability exploitation risks before production release.
   - **Recommended Fix:** Add a `security_scan` stage on every path to production.
   - **Verification Criteria:** Concrete test criteria required to pass.
3. Click the bottom button: **"Simulate Safer Graph in What-If"**.

---

### Step 4: Execute What-If Speculative Simulation
1. You are taken to the **What-If Risk Simulation Console**.
2. Notice the baseline score and verdict.
3. Click the 1-Click preset buttons:
   - Click `+ Security Scan Stage`
   - Click `+ Governance Approval Gate`
   - Click `+ Rollback Plan Stage`
4. Click **Execute Simulation**.
5. Observe the live before/after diff comparison:
   - **Baseline Score:** e.g. 41 / BLOCKED.
   - **Simulated Score:** Dropped to clean score.
   - **Verdict:** Upgraded to `PASS`.
   - **Resolved Violations:** R02, R03, R04 shown in the green resolved list.
   - **Integrity Guarantee:** The original workflow in the database was NOT altered!

---

### Step 5: Log Reviewer Decision & Export Report
1. Return to the **Risk Analysis** page.
2. In the **Record Reviewer Decision** panel, select `Approved`, write notes: `"Reviewed What-If remediation plan with SRE"`, and click **Log Review Decision**.
3. Navigate to **Reports & Export**; preview the complete Markdown report and click **Export JSON** or **Download Markdown (.md)**.
4. Open the **Audit Trail** view and verify the append-only record of all actions with timestamps.
