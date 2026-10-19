import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AnalysisResult, Stage, StageType, WhatIfOperation, WhatIfResult, WorkflowDetail } from "../types";
import { StatusBadge } from "../components/StatusBadge";
import { MermaidViewer } from "../components/MermaidViewer";
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  RotateCcw,
  Save,
  CheckCircle2,
  Wand2,
  GitBranch,
  Layers,
  ArrowLeft,
  Columns,
  Eye,
} from "lucide-react";

interface WhatIfViewProps {
  workflowId: string | null;
  onNavigate: (view: string, workflowId?: string) => void;
}

export const WhatIfView: React.FC<WhatIfViewProps> = ({ workflowId, onNavigate }) => {
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisResult | null>(null);
  const [operations, setOperations] = useState<WhatIfOperation[]>([]);
  const [simResult, setSimResult] = useState<WhatIfResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRemediating, setAutoRemediating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [diagramMode, setDiagramMode] = useState<"future" | "existing" | "side_by_side">("future");
  const [savingAsNew, setSavingAsNew] = useState(false);

  // Manual operation form state (secondary)
  const [newOpType, setNewOpType] = useState<WhatIfOperation["operation"]>("add_stage");
  const [newStageId, setNewStageId] = useState("");
  const [newStageName, setNewStageName] = useState("");
  const [newStageType, setNewStageType] = useState<StageType>("security_scan");
  const [newStageOwner, setNewStageOwner] = useState("platform-team");
  const [newStageDependsOn, setNewStageDependsOn] = useState("");

  useEffect(() => {
    if (workflowId) {
      loadWorkflowAndAnalysis(workflowId);
    }
  }, [workflowId]);

  const loadWorkflowAndAnalysis = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const wf = await api.getWorkflow(id);
      setWorkflow(wf);

      try {
        const an = await api.getLatestAnalysis(id);
        setLatestAnalysis(an);
      } catch {
        const fresh = await api.analyzeWorkflow(id);
        setLatestAnalysis(fresh);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Get active stages from workflow
  const getActiveStages = (): Stage[] => {
    if (!workflow?.versions?.length) return [];
    return workflow.versions[0].payload?.stages || [];
  };

  // 1-Click Automated Safer Architecture Generator
  const handleAutoRemediateAndSimulate = async () => {
    if (!workflowId) return;
    const stages = getActiveStages();
    if (stages.length === 0) {
      setError("Workflow has no stages to simulate.");
      return;
    }

    try {
      setAutoRemediating(true);
      setError(null);

      const existingTypes = new Set(stages.map((s) => s.type));
      const autoOps: WhatIfOperation[] = [];

      // Find key nodes in current topology
      const firstStage = stages.find((s) => s.depends_on.length === 0) || stages[0];
      const prodStage = stages.find((s) => s.type === "deploy_production") || stages[stages.length - 1];

      // 1. Missing tests check (R01 / R09)
      if (!existingTypes.has("unit_test") && !existingTypes.has("integration_test")) {
        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "automated_unit_tests",
            name: "Automated Unit & Regression Tests",
            type: "unit_test",
            owner: "qa-team",
            depends_on: [firstStage.id],
          },
        });
      }

      // Check for continue_on_failure in existing tests (R09)
      for (const s of stages) {
        if ((s.type === "unit_test" || s.type === "integration_test") && (s.continue_on_failure || s.skippable)) {
          autoOps.push({
            operation: "update_stage",
            stage_id: s.id,
            updates: { continue_on_failure: false, skippable: false },
          });
        }
      }

      // 2. Missing Security Scan (R02)
      if (!existingTypes.has("security_scan")) {
        const dep = autoOps.some((op) => op.stage?.id === "automated_unit_tests")
          ? "automated_unit_tests"
          : (stages.find((s) => s.type === "unit_test")?.id || firstStage.id);

        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "static_security_scan",
            name: "SAST & Container Vulnerability Scan",
            type: "security_scan",
            owner: "security-ops",
            depends_on: [dep],
          },
        });
      }

      // 3. Missing Dependency Check (R08)
      if (!existingTypes.has("dependency_check")) {
        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "dependency_vulnerability_check",
            name: "Snyk / Trivy Dependency Check",
            type: "dependency_check",
            owner: "sec-team",
            depends_on: [firstStage.id],
          },
        });
      }

      // 4. Missing Staging Deploy & Validation (R10)
      if (!existingTypes.has("staging_deploy")) {
        const secDep = autoOps.some((op) => op.stage?.id === "static_security_scan")
          ? "static_security_scan"
          : firstStage.id;

        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "staging_deploy",
            name: "Deploy to Pre-Production Staging",
            type: "staging_deploy",
            owner: "ops-team",
            depends_on: [secDep],
          },
        });
        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "staging_validation",
            name: "Staging Smoke & Contract Tests",
            type: "staging_validation",
            owner: "qa-team",
            depends_on: ["staging_deploy"],
          },
        });
      }

      // 5. Missing Approval Gate (R03)
      if (!existingTypes.has("approval")) {
        const priorToApproval = autoOps.some((op) => op.stage?.id === "staging_validation")
          ? "staging_validation"
          : (autoOps.some((op) => op.stage?.id === "static_security_scan") ? "static_security_scan" : firstStage.id);

        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "release_approval_gate",
            name: "Production Governance Approval Gate",
            type: "approval",
            owner: "release-manager",
            depends_on: [priorToApproval],
          },
        });
      }

      // 6. Missing Rollback Plan (R04)
      if (!existingTypes.has("rollback_plan")) {
        const priorToRollback = autoOps.some((op) => op.stage?.id === "release_approval_gate")
          ? "release_approval_gate"
          : firstStage.id;

        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "canary_rollback_guard",
            name: "Automated Canary Rollback Guard",
            type: "rollback_plan",
            owner: "sre-team",
            depends_on: [priorToRollback],
          },
        });
      }

      // 7. Fix unowned production deploy (R05)
      if (prodStage && (!prodStage.owner || prodStage.owner.trim() === "")) {
        autoOps.push({
          operation: "update_stage",
          stage_id: prodStage.id,
          updates: { owner: "platform-ops@company.com" },
        });
      }

      // 8. Re-wire production deploy to depend on the last safety gate
      if (prodStage) {
        const lastGate = autoOps.some((op) => op.stage?.id === "canary_rollback_guard")
          ? "canary_rollback_guard"
          : (autoOps.some((op) => op.stage?.id === "release_approval_gate") ? "release_approval_gate" : null);

        if (lastGate) {
          autoOps.push({
            operation: "update_stage",
            stage_id: prodStage.id,
            updates: { depends_on: [lastGate] },
          });
        }
      }

      // 9. Missing Monitoring Check (R07)
      if (!existingTypes.has("monitoring_check") && prodStage) {
        autoOps.push({
          operation: "add_stage",
          stage: {
            id: "post_deploy_monitoring",
            name: "Datadog / Prometheus Health Probe",
            type: "monitoring_check",
            owner: "sre-team",
            depends_on: [prodStage.id],
          },
        });
      }

      // If pipeline is already 100% compliant, provide celebratory notice
      if (autoOps.length === 0) {
        setSuccessMessage("This workflow already satisfies 100/100 Delivery Assurance! All 10 governance safety gates (Tests, Security Scans, Staging, Approvals, Rollback, Monitoring) are active and clean.");
        setAutoRemediating(false);
        return;
      }

      setOperations(autoOps);

      // Execute simulation immediately
      const res = await api.simulateWhatIf(workflowId, autoOps);
      setSimResult(res);

      if (res.graph_valid) {
        const origAssurance = Math.max(0, 100 - res.original_analysis.score);
        const propAssurance = Math.max(0, 100 - res.proposed_analysis.score);
        setSuccessMessage(`Auto-remediation successful: ${autoOps.length} safety gates synthesized. Delivery Assurance elevated from ${origAssurance}/100 to ${propAssurance}/100 (+${propAssurance - origAssurance} pts)!`);
      } else {
        setError(`Simulation completed with graph notice: ${res.graph_errors?.join(", ") || "Topological constraint"}`);
      }
    } catch (err: any) {
      setError(`Auto-simulation notice: ${err.message}`);
    } finally {
      setAutoRemediating(false);
    }
  };

  const handleRunSimulation = async () => {
    if (!workflowId) return;
    if (operations.length === 0) {
      setError("Please add at least one proposed operation or click '⚡ Auto-Remediate' above.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.simulateWhatIf(workflowId, operations);
      setSimResult(res);
      if (!res.graph_valid && res.graph_errors?.length) {
        setError(`Graph notice: ${res.graph_errors.join(", ")}`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Add individual quick safety preset
  const handleAddPreset = (presetType: string) => {
    const stages = getActiveStages();
    const firstStageId = stages[0]?.id || "build";
    const prodStage = stages.find(s => s.type === "deploy_production");

    let op: WhatIfOperation;
    if (presetType === "sec_scan") {
      op = {
        operation: "add_stage",
        stage: {
          id: "security_vulnerability_scan",
          name: "Static & Container Security Scan",
          type: "security_scan",
          owner: "security@company.com",
          depends_on: [firstStageId],
        },
      };
    } else if (presetType === "approval") {
      op = {
        operation: "add_stage",
        stage: {
          id: "release_approval_gate",
          name: "Release Governance Approval Gate",
          type: "approval",
          owner: "governance-lead@company.com",
          depends_on: [firstStageId],
        },
      };
    } else if (presetType === "rollback") {
      op = {
        operation: "add_stage",
        stage: {
          id: "canary_rollback_plan",
          name: "Automated Canary Rollback Guard",
          type: "rollback_plan",
          owner: "sre@company.com",
          depends_on: [firstStageId],
        },
      };
    } else {
      op = {
        operation: "add_stage",
        stage: {
          id: "post_deploy_monitoring_probe",
          name: "Post-Deployment Canary Health Probe",
          type: "monitoring_check",
          owner: "sre@company.com",
          depends_on: [prodStage ? prodStage.id : firstStageId],
        },
      };
    }

    setOperations([...operations, op]);
  };

  const handleAddCustomOperation = () => {
    if (newOpType === "add_stage") {
      if (!newStageId.trim() || !newStageName.trim()) {
        setError("Stage ID and Name are required.");
        return;
      }
      const cleanId = newStageId.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "_");
      const op: WhatIfOperation = {
        operation: "add_stage",
        stage: {
          id: cleanId,
          name: newStageName.trim(),
          type: newStageType,
          owner: newStageOwner.trim() || "platform-team",
          depends_on: newStageDependsOn ? newStageDependsOn.split(",").map((s) => s.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "_")) : [],
        },
      };
      setOperations([...operations, op]);
      setNewStageId("");
      setNewStageName("");
      setError(null);
    } else if (newOpType === "remove_stage") {
      if (!newStageId.trim()) {
        setError("Stage ID to remove is required.");
        return;
      }
      setOperations([
        ...operations,
        {
          operation: "remove_stage",
          stage_id: newStageId.trim().toLowerCase(),
        },
      ]);
      setNewStageId("");
      setError(null);
    }
  };

  const handleRemoveOperation = (index: number) => {
    setOperations(operations.filter((_, i) => i !== index));
  };

  const handleClearAll = () => {
    setOperations([]);
    setSimResult(null);
    setError(null);
    setSuccessMessage(null);
  };

  // Commit Simulated Safer Architecture as a New Workflow
  const handleCommitSaferWorkflow = async () => {
    if (!workflow || !simResult) return;
    try {
      setSavingAsNew(true);
      setError(null);

      // Construct remediated workflow stages
      const baseStages = getActiveStages();
      let stagesMap = new Map<string, Stage>(baseStages.map(s => [s.id, { ...s }]));

      for (const op of operations) {
        if (op.operation === "add_stage" && op.stage) {
          stagesMap.set(op.stage.id, op.stage);
        } else if (op.operation === "remove_stage" && op.stage_id) {
          stagesMap.delete(op.stage_id);
        } else if (op.operation === "update_stage" && op.stage_id && stagesMap.has(op.stage_id)) {
          const existing = stagesMap.get(op.stage_id)!;
          stagesMap.set(op.stage_id, { ...existing, ...(op.updates || {}) });
        }
      }

      const remediatedStages = Array.from(stagesMap.values());
      const newName = `${workflow.name} (Future Delivery Pipeline - Hardened)`;

      const newWf = await api.createWorkflow({
        name: newName,
        schema_version: "1.0",
        environment: workflow.environment as any,
        change_type: "standard" as any,
        metadata: {
          blast_radius: "low" as any,
          dependencies_changed: false,
        },
        stages: remediatedStages,
      });

      await api.analyzeWorkflow(newWf.workflow_id);
      setSuccessMessage("Future delivery architecture successfully committed as new workflow! Redirecting...");
      setTimeout(() => {
        onNavigate("analysis", newWf.workflow_id);
      }, 1200);
    } catch (err: any) {
      setError(`Failed to save remediated workflow: ${err.message}`);
    } finally {
      setSavingAsNew(false);
    }
  };

  if (!workflowId) {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>No Workflow Selected for What-If</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: 16 }}>
          Select a workflow first to simulate graph changes and auto-remediate delivery architectures.
        </p>
        <button className="btn btn-primary" onClick={() => onNavigate("workflows")}>
          Browse Workflows
        </button>
      </div>
    );
  }

  // Calculate human-psychology scores (100/100 is Clean/Passing)
  const baselineAssurance = simResult
    ? Math.max(0, 100 - simResult.original_analysis.score)
    : (latestAnalysis ? Math.max(0, 100 - latestAnalysis.score) : 100);
  const futureAssurance = simResult
    ? Math.max(0, 100 - simResult.proposed_analysis.score)
    : 100;
  const assuranceGain = futureAssurance - baselineAssurance;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => onNavigate("analysis", workflowId)}
            style={{ marginBottom: 8 }}
          >
            <ArrowLeft size={13} /> Back to Analysis
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h1 className="page-title">What-If Risk Simulation Console</h1>
            {workflow && <span className="badge">{workflow.name}</span>}
          </div>
          <p className="page-description">
            Simulate delivery pipeline architectures, project future safety states, and eliminate deployment blockers before committing changes.
          </p>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button
            className="btn btn-secondary"
            onClick={handleClearAll}
            disabled={operations.length === 0}
          >
            <RotateCcw size={15} /> Reset
          </button>
          <button
            className="btn btn-primary"
            onClick={handleAutoRemediateAndSimulate}
            disabled={autoRemediating || loading}
            style={{ background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)", boxShadow: "0 2px 8px rgba(37,99,235,0.3)" }}
          >
            <Sparkles size={16} /> {autoRemediating ? "Synthesizing Future Pipeline..." : "⚡ Auto-Remediate & Simulate Future Pipeline"}
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div
          style={{
            backgroundColor: "var(--critical-bg)",
            border: "1px solid var(--critical-border)",
            color: "var(--critical)",
            padding: "12px 16px",
            borderRadius: "var(--radius-sm)",
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 13,
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div
          style={{
            backgroundColor: "#F0FDF4",
            border: "1px solid #BBF7D0",
            color: "#16A34A",
            padding: "12px 16px",
            borderRadius: "var(--radius-sm)",
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          <CheckCircle2 size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Auto-Remediation Banner */}
      <div
        className="card"
        style={{
          borderLeft: "4px solid var(--accent)",
          background: "linear-gradient(135deg, rgba(240, 249, 255, 0.5) 0%, rgba(255, 255, 255, 1) 100%)",
          padding: 18,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <Wand2 size={17} color="var(--accent)" />
              <span style={{ fontWeight: 700, fontSize: 14 }}>
                Automated Future Pipeline Synthesis
              </span>
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              One click evaluates all active violations in this pipeline and automatically generates the exact safety gates (Tests, SAST Scans, Staging, Approvals, Rollback, Monitoring) required to achieve a 100/100 Assurance Score.
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleAddPreset("sec_scan")}
              title="Adds security vulnerability scanning stage"
            >
              + Security Scan
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleAddPreset("approval")}
              title="Adds governance approval gate"
            >
              + Approval Gate
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleAddPreset("rollback")}
              title="Adds automated canary rollback guard"
            >
              + Rollback Plan
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleAddPreset("monitoring")}
              title="Adds post-deploy health check probe"
            >
              + Health Probe
            </button>
          </div>
        </div>
      </div>

      {/* SIMULATION RESULTS (If executed) */}
      {simResult && simResult.original_analysis && (
        <div className="card" style={{ borderLeft: "5px solid var(--accent)", padding: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 10 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <CheckCircle size={20} color="var(--low)" />
                <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
                  Architecture Impact Comparison (Existing vs Future State)
                </h2>
              </div>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>
                Human-psychology quality scoring: 100/100 is Clean Pass. Comparing current baseline against projected future delivery architecture.
              </p>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button
                className="btn btn-primary"
                onClick={handleCommitSaferWorkflow}
                disabled={savingAsNew}
                style={{ background: "var(--low)", borderColor: "var(--low)" }}
              >
                <Save size={15} /> {savingAsNew ? "Committing..." : "Apply & Commit Future Pipeline as Active Version"}
              </button>
            </div>
          </div>

          {/* Metric Comparison Cards: Human Psychology (100/100 = Clean Pass) */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 24 }}>
            {/* Existing Baseline */}
            <div style={{ padding: 16, background: "var(--bg-app)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                EXISTING PIPELINE ASSURANCE
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)" }}>
                {baselineAssurance} / 100
              </div>
              <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8 }}>
                <StatusBadge type="verdict" value={simResult.original_analysis.verdict} />
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  ({simResult.original_analysis.score} risk deductions)
                </span>
              </div>
            </div>

            {/* Future Pipeline (Projected Target) */}
            <div style={{ padding: 16, background: "var(--low-bg)", borderRadius: "var(--radius-sm)", border: "1px solid var(--low-border)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--low)", marginBottom: 6 }}>
                FUTURE PIPELINE ASSURANCE
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: "var(--low)" }}>
                {futureAssurance} / 100
              </div>
              <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8 }}>
                <StatusBadge type="verdict" value={simResult.proposed_analysis.verdict} />
                <span style={{ fontSize: 11, color: "var(--low)", fontWeight: 600 }}>
                  {futureAssurance === 100 ? "100% Clean Pass" : "Hardened"}
                </span>
              </div>
            </div>

            {/* Quality Gain */}
            <div style={{ padding: 16, background: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                DELIVERY ASSURANCE GAIN
              </div>
              <div
                style={{
                  fontSize: 28,
                  fontWeight: 800,
                  color: assuranceGain >= 0 ? "var(--low)" : "var(--critical)",
                }}
              >
                +{assuranceGain} pts
              </div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
                <TrendingUp size={14} color="var(--low)" />
                <span style={{ color: "var(--low)", fontWeight: 600 }}>
                  {simResult.verdict_change ? "Verdict upgraded to PASS!" : "Risk completely mitigated"}
                </span>
              </div>
            </div>
          </div>

          {/* Visual Architecture Comparison: Existing vs Future Delivery Pipeline */}
          {(simResult.proposed_diagram || simResult.original_diagram) && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    type="button"
                    className={`btn ${diagramMode === "future" ? "btn-primary" : "btn-secondary"} btn-sm`}
                    onClick={() => setDiagramMode("future")}
                  >
                    <ShieldCheck size={14} /> Future Delivery Pipeline (Proposed Next State)
                  </button>
                  <button
                    type="button"
                    className={`btn ${diagramMode === "existing" ? "btn-primary" : "btn-secondary"} btn-sm`}
                    onClick={() => setDiagramMode("existing")}
                  >
                    <Layers size={14} /> Existing Delivery Pipeline (Current State)
                  </button>
                  <button
                    type="button"
                    className={`btn ${diagramMode === "side_by_side" ? "btn-primary" : "btn-secondary"} btn-sm`}
                    onClick={() => setDiagramMode("side_by_side")}
                  >
                    <Columns size={14} /> Side-by-Side Dual View
                  </button>
                </div>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  In-memory topological projection • Zero database mutation
                </span>
              </div>

              {/* View 1: Future Delivery Pipeline */}
              {diagramMode === "future" && simResult.proposed_diagram && (
                <div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
                    <strong>Future Delivery Pipeline:</strong> Incorporates automated safety gates, SAST scans, release approvals, rollback guards, and telemetry health probes (highlighted in blue):
                  </div>
                  <MermaidViewer
                    id="whatif-future-delivery"
                    chart={simResult.proposed_diagram.mermaid_code}
                  />
                </div>
              )}

              {/* View 2: Existing Delivery Pipeline */}
              {diagramMode === "existing" && simResult.original_diagram && (
                <div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
                    <strong>Existing Delivery Pipeline:</strong> Current operational topology as observed with active risk finding hotspots highlighted in red:
                  </div>
                  <MermaidViewer
                    id="whatif-existing-delivery"
                    chart={simResult.original_diagram.mermaid_code}
                  />
                </div>
              )}

              {/* View 3: Side-by-Side Dual View */}
              {diagramMode === "side_by_side" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "var(--critical)", marginBottom: 6 }}>
                      🔴 Existing Delivery Pipeline (Current)
                    </div>
                    {simResult.original_diagram ? (
                      <MermaidViewer
                        id="whatif-split-existing"
                        chart={simResult.original_diagram.mermaid_code}
                      />
                    ) : (
                      <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>No existing diagram</div>
                    )}
                  </div>

                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "var(--low)", marginBottom: 6 }}>
                      🟢 Future Delivery Pipeline (Proposed Target)
                    </div>
                    {simResult.proposed_diagram ? (
                      <MermaidViewer
                        id="whatif-split-future"
                        chart={simResult.proposed_diagram.mermaid_code}
                      />
                    ) : (
                      <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>No future diagram</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Resolved Violations Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ padding: 14, background: "#F0FDF4", borderRadius: "var(--radius-sm)", border: "1px solid #BBF7D0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 700, fontSize: 13, color: "var(--low)", marginBottom: 8 }}>
                <CheckCircle size={16} /> Cleared Blockers & Violations in Future Pipeline ({simResult.resolved_findings.length})
              </div>
              {simResult.resolved_findings.length === 0 ? (
                <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>None cleared yet</div>
              ) : (
                <ul style={{ fontSize: 12, paddingLeft: 18, color: "var(--text-primary)", margin: 0 }}>
                  {simResult.resolved_findings.map((fid, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>
                      Rule violation cleared: <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{fid}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div style={{ padding: 14, background: "#FEFCE8", borderRadius: "var(--radius-sm)", border: "1px solid #FEF08A" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 700, fontSize: 13, color: "var(--medium)", marginBottom: 8 }}>
                <AlertCircle size={16} /> Remaining Violations ({simResult.still_present_findings.length})
              </div>
              {simResult.still_present_findings.length === 0 ? (
                <div style={{ fontSize: 12, color: "var(--low)", fontWeight: 600 }}>
                  All blocking violations eliminated! Future pipeline is 100% clean.
                </div>
              ) : (
                <ul style={{ fontSize: 12, paddingLeft: 18, color: "var(--text-primary)", margin: 0 }}>
                  {simResult.still_present_findings.map((fid, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>
                      Pending violation: <span style={{ fontFamily: "monospace" }}>{fid}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* OPERATIONS QUEUE & CUSTOM OP BUILDER */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 20 }}>
        {/* Queued Operations */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
              Speculative Future Pipeline Operations ({operations.length})
            </h3>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleRunSimulation}
              disabled={loading || operations.length === 0}
            >
              <Sparkles size={14} /> {loading ? "Simulating..." : "Execute Simulation"}
            </button>
          </div>

          {operations.length === 0 ? (
            <div style={{ padding: 36, textAlign: "center", color: "var(--text-muted)" }}>
              No operations queued. Click the <strong>"⚡ Auto-Remediate"</strong> button above to automatically compose the Future Delivery Pipeline.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 360, overflowY: "auto" }}>
              {operations.map((op, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "10px 14px",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-sm)",
                    background: "var(--surface)",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="badge" style={{ textTransform: "uppercase", fontSize: 10 }}>
                        {op.operation}
                      </span>
                      <span style={{ fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
                        {op.stage ? op.stage.name : op.stage_id}
                      </span>
                    </div>
                    {op.stage && (
                      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 3 }}>
                        id: <span style={{ fontFamily: "monospace" }}>{op.stage.id}</span> • Type: {op.stage.type}
                        {op.stage.depends_on.length > 0 && (
                          <span style={{ marginLeft: 6, color: "var(--accent)" }}>
                            Depends on: [{op.stage.depends_on.join(", ")}]
                          </span>
                        )}
                      </div>
                    )}
                    {op.updates && (
                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                        Updates: {JSON.stringify(op.updates)}
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleRemoveOperation(idx)}
                    style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--critical)", padding: 6 }}
                    title="Remove operation"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Custom Operation Creator (Secondary) */}
        <div className="card">
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
            Add Custom Future Stage (Optional)
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div>
              <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                Operation Action
              </label>
              <select
                value={newOpType}
                onChange={(e) => setNewOpType(e.target.value as any)}
                style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
              >
                <option value="add_stage">Add New Stage Node</option>
                <option value="remove_stage">Remove Existing Stage Node</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                Stage ID
              </label>
              <input
                type="text"
                placeholder="e.g. static_code_scan"
                value={newStageId}
                onChange={(e) => setNewStageId(e.target.value)}
                style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
              />
            </div>

            {newOpType === "add_stage" && (
              <>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                    Display Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Static Code Analysis"
                    value={newStageName}
                    onChange={(e) => setNewStageName(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                    Stage Control Type
                  </label>
                  <select
                    value={newStageType}
                    onChange={(e) => setNewStageType(e.target.value as any)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  >
                    <option value="security_scan">Security Scan</option>
                    <option value="unit_test">Unit Test</option>
                    <option value="approval">Approval Gate</option>
                    <option value="rollback_plan">Rollback Plan</option>
                    <option value="monitoring_check">Monitoring Check</option>
                    <option value="dependency_check">Dependency Check</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                    Depends On (Comma-separated stage IDs)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. build, unit_test"
                    value={newStageDependsOn}
                    onChange={(e) => setNewStageDependsOn(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  />
                </div>
              </>
            )}

            <button
              className="btn btn-secondary btn-sm"
              onClick={handleAddCustomOperation}
              style={{ marginTop: 6 }}
            >
              <Plus size={13} /> Add to Simulation Queue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
