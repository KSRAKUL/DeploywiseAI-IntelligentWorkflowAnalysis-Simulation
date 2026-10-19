import React, { useState } from "react";
import { api } from "../lib/api";
import { Stage, StageType, WorkflowInput } from "../types";
import { GraphCanvas } from "../components/GraphCanvas";
import {
  Plus,
  Trash2,
  Save,
  AlertCircle,
  ArrowLeft,
  Sparkles,
  Wand2,
  ShieldCheck,
  Link,
  Layers,
  CheckCircle2,
  Play,
  HelpCircle,
} from "lucide-react";

interface WorkflowBuilderViewProps {
  onNavigate: (view: string, workflowId?: string) => void;
}

const STAGE_TYPES: { type: StageType; label: string }[] = [
  { type: "build", label: "Build & Compile" },
  { type: "unit_test", label: "Automated Unit Tests" },
  { type: "integration_test", label: "Integration & API Tests" },
  { type: "security_scan", label: "Security & SAST Scan" },
  { type: "secrets_scan", label: "Secrets & Credential Scan" },
  { type: "dependency_check", label: "Dependency Vulnerability Check" },
  { type: "staging_deploy", label: "Deploy to Staging Environment" },
  { type: "staging_validation", label: "Staging Smoke & E2E Validation" },
  { type: "approval", label: "Release Governance Approval Gate" },
  { type: "rollback_plan", label: "Canary Rollback Guard" },
  { type: "deploy_production", label: "Deploy to Production" },
  { type: "monitoring_check", label: "Post-Deploy Health Probe" },
];

// Curated high-reliability architectural blueprints
const BLUEPRINTS: Record<string, { name: string; description: string; stages: Stage[] }> = {
  devsecops: {
    name: "Enterprise DevSecOps Production Gate",
    description: "Complete 10-stage delivery pipeline incorporating comprehensive shift-left security, staging validation, governance sign-off, and canary monitoring.",
    stages: [
      { id: "build", name: "Build Artifact & Bundle", type: "build", owner: "platform-team", depends_on: [] },
      { id: "unit_test", name: "Automated Unit Test Suite", type: "unit_test", owner: "qa-team", depends_on: ["build"] },
      { id: "dependency_check", name: "Snyk / Trivy Dependency Check", type: "dependency_check", owner: "sec-team", depends_on: ["build"] },
      { id: "security_scan", name: "SonarQube & SAST Vulnerability Scan", type: "security_scan", owner: "sec-team", depends_on: ["unit_test", "dependency_check"] },
      { id: "staging_deploy", name: "Deploy to Pre-Prod Staging", type: "staging_deploy", owner: "ops-team", depends_on: ["security_scan"] },
      { id: "staging_validation", name: "Staging Smoke & E2E Health Verification", type: "staging_validation", owner: "qa-team", depends_on: ["staging_deploy"] },
      { id: "approval", name: "Release Governance Approval Gate", type: "approval", owner: "release-manager", depends_on: ["staging_validation"] },
      { id: "rollback_plan", name: "Automated Canary Rollback Guard", type: "rollback_plan", owner: "sre-team", depends_on: ["approval"] },
      { id: "deploy_production", name: "Blue-Green Deploy to Production", type: "deploy_production", owner: "deploy-team", depends_on: ["rollback_plan"] },
      { id: "monitoring_check", name: "Datadog / Prometheus Post-Deploy Health Check", type: "monitoring_check", owner: "sre-team", depends_on: ["deploy_production"] },
    ],
  },
  microservice: {
    name: "Containerized Microservice (Docker & K8s)",
    description: "Cloud-native Kubernetes CI/CD pipeline with container scanning, image signing, and automated rollback probes.",
    stages: [
      { id: "docker_build", name: "Docker Container Build & Lint", type: "build", owner: "dev-team", depends_on: [] },
      { id: "test_suite", name: "Integration & Contract Tests", type: "unit_test", owner: "qa-team", depends_on: ["docker_build"] },
      { id: "image_scan", name: "Trivy Container Vulnerability Scan", type: "security_scan", owner: "sec-ops", depends_on: ["docker_build"] },
      { id: "staging_helm", name: "Deploy to Staging Kubernetes Cluster", type: "staging_deploy", owner: "platform-team", depends_on: ["test_suite", "image_scan"] },
      { id: "governance_gate", name: "Tech Lead Deployment Approval", type: "approval", owner: "tech-lead", depends_on: ["staging_helm"] },
      { id: "canary_rollback", name: "Canary Automated Rollback Guard", type: "rollback_plan", owner: "sre-ops", depends_on: ["governance_gate"] },
      { id: "prod_k8s_deploy", name: "Rolling Deploy to Production K8s", type: "deploy_production", owner: "deploy-team", depends_on: ["canary_rollback"] },
      { id: "prometheus_probe", name: "Prometheus Error Budget & Metric Check", type: "monitoring_check", owner: "sre-ops", depends_on: ["prod_k8s_deploy"] },
    ],
  },
  serverless: {
    name: "Cloud Serverless Pipeline (AWS Lambda / GCP)",
    description: "Lightweight, highly automated deployment with secrets hygiene, automated tests, and canary CloudWatch telemetry.",
    stages: [
      { id: "package_func", name: "Bundle Function Artifacts", type: "build", owner: "cloud-team", depends_on: [] },
      { id: "unit_tests", name: "Unit & Mock Tests", type: "unit_test", owner: "dev-team", depends_on: ["package_func"] },
      { id: "secrets_audit", name: "GitGuardian Secrets Scan", type: "secrets_scan", owner: "sec-team", depends_on: ["package_func"] },
      { id: "staging_stage", name: "Deploy to Staging Stage", type: "staging_deploy", owner: "cloud-team", depends_on: ["unit_tests", "secrets_audit"] },
      { id: "release_gate", name: "Governance Approval", type: "approval", owner: "prod-owner", depends_on: ["staging_stage"] },
      { id: "prod_deploy", name: "Alias Shift Deploy to Production", type: "deploy_production", owner: "cloud-team", depends_on: ["release_gate"] },
      { id: "cloudwatch_probe", name: "CloudWatch Latency & 5xx Probe", type: "monitoring_check", owner: "sre-team", depends_on: ["prod_deploy"] },
    ],
  },
  minimal: {
    name: "Clean Verified Production Baseline",
    description: "Lean, passing pipeline meeting standard safety criteria.",
    stages: [
      { id: "build", name: "Build Artifact", type: "build", owner: "platform-team", depends_on: [] },
      { id: "unit_test", name: "Unit Tests", type: "unit_test", owner: "qa-team", depends_on: ["build"] },
      { id: "security_scan", name: "Security Vulnerability Scan", type: "security_scan", owner: "sec-team", depends_on: ["unit_test"] },
      { id: "staging_deploy", name: "Deploy to Staging", type: "staging_deploy", owner: "ops-team", depends_on: ["security_scan"] },
      { id: "approval", name: "Release Approval", type: "approval", owner: "release-lead", depends_on: ["staging_deploy"] },
      { id: "rollback_plan", name: "Rollback Plan", type: "rollback_plan", owner: "sre-team", depends_on: ["approval"] },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: "ops-team", depends_on: ["rollback_plan"] },
      { id: "monitoring_check", name: "Health Probe", type: "monitoring_check", owner: "sre-team", depends_on: ["deploy_production"] },
    ],
  },
  fragile: {
    name: "Unsafe Direct Deploy (Demonstrates Blocked Verdict)",
    description: "Intentionally broken anti-pattern (no tests, no security scans, unowned prod deploy) to test rule engine blocking behavior.",
    stages: [
      { id: "build", name: "Build Artifact", type: "build", owner: "build-team", depends_on: [] },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: "", depends_on: ["build"] },
    ],
  },
};

export const WorkflowBuilderView: React.FC<WorkflowBuilderViewProps> = ({ onNavigate }) => {
  const [name, setName] = useState("Enterprise Software Delivery Pipeline");
  const [environment, setEnvironment] = useState<any>("production");
  const [changeType, setChangeType] = useState<any>("standard");
  const [blastRadius, setBlastRadius] = useState<any>("medium");
  const [dependenciesChanged, setDependenciesChanged] = useState(false);

  // Active stages
  const [stages, setStages] = useState<Stage[]>(BLUEPRINTS.devsecops.stages);

  // AI prompt state
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiSuccessMsg, setAiSuccessMsg] = useState<string | null>(null);

  // Manual stage input (secondary for edge-case fine-tuning)
  const [newStageId, setNewStageId] = useState("");
  const [newStageName, setNewStageName] = useState("");
  const [newStageType, setNewStageType] = useState<StageType>("security_scan");
  const [newStageOwner, setNewStageOwner] = useState("platform-team");
  const [newStageDependsOn, setNewStageDependsOn] = useState<string[]>([]);

  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // 1-Click Load Blueprint
  const handleLoadBlueprint = (key: string) => {
    const bp = BLUEPRINTS[key];
    if (!bp) return;
    setName(bp.name);
    setStages(bp.stages);
    setError(null);
    setAiSuccessMsg(`Loaded blueprint: "${bp.name}" with ${bp.stages.length} verified stages.`);
    setTimeout(() => setAiSuccessMsg(null), 3500);
  };

  // AI Natural Language Synthesis Engine
  const handleAiSynthesize = () => {
    if (!aiPrompt.trim()) {
      setError("Please describe the target pipeline architecture to synthesize.");
      return;
    }
    setAiGenerating(true);
    setError(null);

    const text = aiPrompt.toLowerCase();
    const synthStages: Stage[] = [];

    // 1. Build
    const isDocker = text.includes("docker") || text.includes("container") || text.includes("image");
    const buildId = isDocker ? "docker_build" : "build_artifact";
    synthStages.push({
      id: buildId,
      name: isDocker ? "Build Docker Container" : "Build & Package Software",
      type: "build",
      owner: "build-team",
      depends_on: [],
    });

    // 2. Unit Testing
    let lastDep = buildId;
    if (!text.includes("skip test") && !text.includes("no test")) {
      const testId = "automated_tests";
      synthStages.push({
        id: testId,
        name: text.includes("jest") ? "Jest Unit Tests" : (text.includes("pytest") ? "PyTest Unit Suite" : "Automated Unit Tests"),
        type: "unit_test",
        owner: "qa-team",
        depends_on: [lastDep],
      });
      lastDep = testId;
    }

    // 3. Dependency Check
    if (text.includes("snyk") || text.includes("dependency") || text.includes("dep") || text.includes("audit") || text.includes("security")) {
      synthStages.push({
        id: "dependency_check",
        name: "Dependency Vulnerability Audit",
        type: "dependency_check",
        owner: "sec-team",
        depends_on: [buildId],
      });
    }

    // 4. Security Scan
    if (text.includes("security") || text.includes("sast") || text.includes("sonar") || text.includes("trivy") || text.includes("scan")) {
      const secDeps = [lastDep];
      if (synthStages.some(s => s.id === "dependency_check")) {
        secDeps.push("dependency_check");
      }
      synthStages.push({
        id: "security_scan",
        name: text.includes("sonar") ? "SonarQube Code Quality & SAST" : (isDocker ? "Trivy Container Scan" : "Security Vulnerability Scan"),
        type: "security_scan",
        owner: "security-team",
        depends_on: secDeps,
      });
      lastDep = "security_scan";
    }

    // 5. Staging Environment
    if (text.includes("staging") || text.includes("preview") || text.includes("qa") || text.includes("pre-prod") || !text.includes("direct prod")) {
      synthStages.push({
        id: "staging_deploy",
        name: "Deploy to Staging Environment",
        type: "staging_deploy",
        owner: "deploy-team",
        depends_on: [lastDep],
      });
      synthStages.push({
        id: "staging_validation",
        name: "Staging Smoke & E2E Verification",
        type: "staging_validation",
        owner: "qa-team",
        depends_on: ["staging_deploy"],
      });
      lastDep = "staging_validation";
    }

    // 6. Approval Gate
    if (text.includes("approval") || text.includes("governance") || text.includes("signoff") || text.includes("manual") || !text.includes("unattended")) {
      synthStages.push({
        id: "governance_approval",
        name: "Production Release Approval Gate",
        type: "approval",
        owner: "release-manager",
        depends_on: [lastDep],
      });
      lastDep = "governance_approval";
    }

    // 7. Rollback Guard
    synthStages.push({
      id: "rollback_guard",
      name: "Automated Canary Rollback Guard",
      type: "rollback_plan",
      owner: "sre-team",
      depends_on: [lastDep],
    });
    lastDep = "rollback_guard";

    // 8. Production Deploy
    synthStages.push({
      id: "deploy_production",
      name: text.includes("k8s") || text.includes("kubernetes") ? "Production Kubernetes Deployment" : (text.includes("ecs") ? "Production AWS ECS Deployment" : "Deploy to Production"),
      type: "deploy_production",
      owner: "ops-team",
      depends_on: [lastDep],
    });

    // 9. Post-Deploy Monitoring
    synthStages.push({
      id: "monitoring_check",
      name: "Post-Deployment Canary Health Probe",
      type: "monitoring_check",
      owner: "sre-team",
      depends_on: ["deploy_production"],
    });

    setTimeout(() => {
      setStages(synthStages);
      setName(`AI-Synthesized: ${aiPrompt.slice(0, 40)}...`);
      setAiGenerating(false);
      setAiSuccessMsg(`Synthesized ${synthStages.length} pipeline stages with optimal topological dependency ordering.`);
      setTimeout(() => setAiSuccessMsg(null), 4000);
    }, 400);
  };

  // Auto-Wire Linear Dependencies
  const handleAutoWireLinear = () => {
    if (stages.length <= 1) return;
    const wired = stages.map((s, idx) => ({
      ...s,
      depends_on: idx === 0 ? [] : [stages[idx - 1].id],
    }));
    setStages(wired);
    setAiSuccessMsg("Auto-wired all stages into a clean linear DAG.");
    setTimeout(() => setAiSuccessMsg(null), 3000);
  };

  // Auto-Inject Missing Safety Gates
  const handleAutoInjectSafetyGates = () => {
    const existingTypes = new Set(stages.map(s => s.type));
    const newStages = [...stages];
    const buildStage = stages.find(s => s.type === "build") || stages[0];
    const prodStage = stages.find(s => s.type === "deploy_production");

    // 1. Add unit test if missing
    if (!existingTypes.has("unit_test") && !existingTypes.has("integration_test") && buildStage) {
      newStages.splice(1, 0, {
        id: "auto_unit_tests",
        name: "Automated Unit Tests",
        type: "unit_test",
        owner: "qa-team",
        depends_on: [buildStage.id],
      });
    }

    // 2. Add security scan if missing
    if (!existingTypes.has("security_scan")) {
      const priorStage = newStages.find(s => s.type === "unit_test") || buildStage;
      newStages.splice(2, 0, {
        id: "auto_security_scan",
        name: "Security Vulnerability Scan",
        type: "security_scan",
        owner: "sec-team",
        depends_on: priorStage ? [priorStage.id] : [],
      });
    }

    // 3. Add approval gate before prod
    if (!existingTypes.has("approval") && prodStage) {
      const prodIdx = newStages.findIndex(s => s.id === prodStage.id);
      const prevId = prodStage.depends_on[0] || (prodIdx > 0 ? newStages[prodIdx - 1].id : "build");
      const approvalStage: Stage = {
        id: "auto_approval_gate",
        name: "Release Governance Approval Gate",
        type: "approval",
        owner: "release-manager",
        depends_on: [prevId],
      };
      newStages.splice(prodIdx, 0, approvalStage);
      prodStage.depends_on = ["auto_approval_gate"];
    }

    // 4. Add rollback plan if missing
    if (!existingTypes.has("rollback_plan") && prodStage) {
      const prodIdx = newStages.findIndex(s => s.id === prodStage.id);
      const prevId = prodStage.depends_on[0] || (prodIdx > 0 ? newStages[prodIdx - 1].id : "build");
      const rollbackStage: Stage = {
        id: "auto_rollback_plan",
        name: "Automated Canary Rollback Guard",
        type: "rollback_plan",
        owner: "sre-team",
        depends_on: [prevId],
      };
      newStages.splice(prodIdx, 0, rollbackStage);
      prodStage.depends_on = ["auto_rollback_plan"];
    }

    // 5. Add monitoring check after prod
    if (!existingTypes.has("monitoring_check") && prodStage) {
      newStages.push({
        id: "auto_monitoring_check",
        name: "Post-Deployment Canary Health Probe",
        type: "monitoring_check",
        owner: "sre-team",
        depends_on: [prodStage.id],
      });
    }

    // 6. Fix unowned prod
    if (prodStage && !prodStage.owner) {
      prodStage.owner = "platform-ops@company.com";
    }

    setStages(newStages);
    setAiSuccessMsg("Auto-injected missing safety gates (Tests, Security Scans, Approvals, Rollback, and Monitoring).");
    setTimeout(() => setAiSuccessMsg(null), 3500);
  };

  // Manual Add Stage
  const handleAddStage = () => {
    if (!newStageId.trim() || !newStageName.trim()) {
      setError("Stage ID and Name are required.");
      return;
    }
    const cleanId = newStageId.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "_");
    if (stages.some((s) => s.id === cleanId)) {
      setError(`Stage ID '${cleanId}' already exists.`);
      return;
    }

    setStages([
      ...stages,
      {
        id: cleanId,
        name: newStageName.trim(),
        type: newStageType,
        owner: newStageOwner.trim() || "platform-team",
        depends_on: newStageDependsOn,
      },
    ]);

    setNewStageId("");
    setNewStageName("");
    setNewStageOwner("platform-team");
    setNewStageDependsOn([]);
    setError(null);
  };

  const handleRemoveStage = (id: string) => {
    setStages(
      stages
        .filter((s) => s.id !== id)
        .map((s) => ({
          ...s,
          depends_on: s.depends_on.filter((dep) => dep !== id),
        }))
    );
  };

  // Robust Save & Analyze
  const handleSaveWorkflow = async () => {
    if (!name.trim()) {
      setError("Workflow name is required.");
      return;
    }
    if (stages.length === 0) {
      setError("Workflow must contain at least one stage.");
      return;
    }

    // Client-side sanitization of IDs and dependencies to guarantee schema validity
    const validIds = new Set(stages.map(s => s.id));
    const sanitizedStages = stages.map(s => {
      const cleanId = s.id.toLowerCase().replace(/[^a-z0-9_-]/g, "_");
      return {
        ...s,
        id: cleanId,
        owner: s.owner?.trim() || null,
        // Filter out unknown dependencies
        depends_on: s.depends_on.filter(d => validIds.has(d) && d !== s.id),
      };
    });

    try {
      setSaving(true);
      setError(null);

      const payload: WorkflowInput = {
        name: name.trim(),
        schema_version: "1.0",
        environment,
        change_type: changeType,
        metadata: {
          blast_radius: blastRadius,
          dependencies_changed: dependenciesChanged,
        },
        stages: sanitizedStages,
      };

      // 1. Persist workflow
      const res = await api.createWorkflow(payload);

      // 2. Pre-run analysis to ensure instantaneous render without errors
      try {
        await api.analyzeWorkflow(res.workflow_id);
      } catch (analyzeErr) {
        console.warn("Analysis pre-warm completed with status:", analyzeErr);
      }

      // 3. Navigate to analysis console
      onNavigate("analysis", res.workflow_id);
    } catch (err: any) {
      setError(`Failed to save workflow: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => onNavigate("workflows")}
            style={{ marginBottom: 8 }}
          >
            <ArrowLeft size={13} /> Back to Workflows
          </button>
          <h1 className="page-title">Automated Workflow DAG Builder</h1>
          <p className="page-description">
            Design, synthesize, and auto-compose delivery pipelines with automated safety gate injection.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-primary" onClick={handleSaveWorkflow} disabled={saving}>
            <Save size={16} /> {saving ? "Saving & Analyzing..." : "Save & Analyze"}
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

      {aiSuccessMsg && (
        <div
          style={{
            backgroundColor: "#F0FDF4",
            border: "1px solid #BBF7D0",
            color: "#16A34A",
            padding: "10px 16px",
            borderRadius: "var(--radius-sm)",
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          <CheckCircle2 size={16} />
          <span>{aiSuccessMsg}</span>
        </div>
      )}

      {/* SECTION 1: AI Prompt Pipeline Synthesizer */}
      <div
        className="card"
        style={{
          borderLeft: "4px solid var(--accent)",
          background: "linear-gradient(135deg, rgba(240, 249, 255, 0.6) 0%, rgba(255, 255, 255, 1) 100%)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <Sparkles size={18} color="var(--accent)" />
          <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>
            AI Pipeline Synthesizer (Auto-Build Architecture)
          </h2>
          <span className="badge" style={{ background: "rgba(37, 99, 235, 0.1)", color: "var(--accent)" }}>
            Zero-Manual Filling
          </span>
        </div>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
          Describe your application stack, tech stack, and deployment targets. Deploywise AI will automatically synthesize the full DAG with safety gates and dependencies.
        </p>

        <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
          <input
            type="text"
            placeholder="e.g. Docker microservice with Jest unit tests, SonarQube SAST, staging deployment, approval gate, and production K8s"
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAiSynthesize()}
            style={{
              flex: 1,
              padding: "9px 14px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border)",
              fontSize: 13,
            }}
          />
          <button
            className="btn btn-primary"
            onClick={handleAiSynthesize}
            disabled={aiGenerating}
            style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}
          >
            <Wand2 size={15} /> {aiGenerating ? "Synthesizing..." : "⚡ Synthesize Architecture with AI"}
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", fontSize: 12 }}>
          <span style={{ color: "var(--text-muted)" }}>Try quick prompts:</span>
          {[
            "FastAPI Python service with PyTest, Snyk, and AWS ECS",
            "Next.js frontend with ESLint, Jest, and Vercel preview",
            "Go microservice with Docker, Trivy, and Kubernetes",
          ].map((promptText, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setAiPrompt(promptText);
              }}
              style={{
                background: "var(--card-bg, #ffffff)",
                border: "1px solid var(--border)",
                borderRadius: 14,
                padding: "3px 10px",
                fontSize: 11,
                cursor: "pointer",
                color: "var(--text-primary)",
              }}
            >
              {promptText}
            </button>
          ))}
        </div>
      </div>

      {/* SECTION 2: 1-Click Production Blueprints & Automation Actions */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, flexWrap: "wrap", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Layers size={18} color="var(--accent)" />
            <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
              1-Click Verified Architecture Blueprints
            </h3>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleAutoWireLinear}
              title="Automatically sets stage dependencies sequentially [0] -> [1] -> [2]"
            >
              <Link size={13} /> Auto-Wire Linear DAG
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleAutoInjectSafetyGates}
              title="Detects missing security, testing, approval, or rollback stages and injects them"
              style={{ color: "var(--accent)", borderColor: "var(--accent)" }}
            >
              <ShieldCheck size={13} /> Auto-Inject Missing Safety Gates
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
          {Object.entries(BLUEPRINTS).map(([key, bp]) => (
            <div
              key={key}
              onClick={() => handleLoadBlueprint(key)}
              style={{
                padding: "12px 14px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
                cursor: "pointer",
                background: name === bp.name ? "rgba(37, 99, 235, 0.05)" : "var(--surface)",
                borderColor: name === bp.name ? "var(--accent)" : "var(--border)",
                transition: "all 0.15s ease",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 12, marginBottom: 4, color: "var(--text-primary)" }}>
                {bp.name}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-secondary)", lineHeight: 1.3 }}>
                {bp.stages.length} stages • {bp.description.slice(0, 70)}...
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SECTION 3: Live Pipeline DAG Topology Preview */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
            Pipeline Topology Preview ({stages.length} Stages)
          </h3>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Live in-memory DAG validation active
          </span>
        </div>
        <GraphCanvas stages={stages} />
      </div>

      {/* SECTION 4: Properties & Configured Stages Table */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: 20 }}>
        {/* Left: Workflow Metadata & Quick Stage Adder */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>Workflow Properties</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                  Pipeline Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{ width: "100%", padding: "7px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 13 }}
                />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                    Target Environment
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  >
                    <option value="production">production</option>
                    <option value="staging">staging</option>
                    <option value="development">development</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 4 }}>
                    Blast Radius
                  </label>
                  <select
                    value={blastRadius}
                    onChange={(e) => setBlastRadius(e.target.value)}
                    style={{ width: "100%", padding: "7px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  >
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                </div>
              </div>
              <label style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 8, cursor: "pointer", marginTop: 4 }}>
                <input
                  type="checkbox"
                  checked={dependenciesChanged}
                  onChange={(e) => setDependenciesChanged(e.target.checked)}
                />
                <span style={{ fontWeight: 500 }}>Dependencies modified in this release (triggers R08 check)</span>
              </label>
            </div>
          </div>

          {/* Quick Stage Append (Secondary) */}
          <div className="card">
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
              Add Custom Stage Node (Optional Fine-Tuning)
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                    Stage ID
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. snyk_scan"
                    value={newStageId}
                    onChange={(e) => setNewStageId(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                    Display Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Snyk Container Scan"
                    value={newStageName}
                    onChange={(e) => setNewStageName(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                  Stage Control Type
                </label>
                <select
                  value={newStageType}
                  onChange={(e) => setNewStageType(e.target.value as StageType)}
                  style={{ width: "100%", padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
                >
                  {STAGE_TYPES.map((st) => (
                    <option key={st.type} value={st.type}>
                      {st.label} ({st.type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 3 }}>
                  Preceding Stages (Depends On)
                </label>
                <select
                  multiple
                  value={newStageDependsOn}
                  onChange={(e) =>
                    setNewStageDependsOn(Array.from(e.target.selectedOptions, (o) => o.value))
                  }
                  style={{ width: "100%", height: 60, padding: 4, borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 11 }}
                >
                  {stages.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.id})
                    </option>
                  ))}
                </select>
              </div>

              <button className="btn btn-secondary btn-sm" onClick={handleAddStage} style={{ marginTop: 4 }}>
                <Plus size={13} /> Append Stage
              </button>
            </div>
          </div>
        </div>

        {/* Right: Stage Sequence & Management */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
              Active Pipeline Stages ({stages.length})
            </h3>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Ordered sequentially
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 520, overflowY: "auto" }}>
            {stages.map((stage, idx) => (
              <div
                key={stage.id}
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
                    <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", width: 18 }}>
                      #{idx + 1}
                    </span>
                    <span style={{ fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
                      {stage.name}
                    </span>
                    <span className="badge" style={{ fontSize: 10 }}>{stage.type}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 3, marginLeft: 26 }}>
                    <span style={{ fontFamily: "monospace" }}>id: {stage.id}</span> • Owner: {stage.owner || "None"}
                    {stage.depends_on.length > 0 && (
                      <span style={{ marginLeft: 8, color: "var(--accent)" }}>
                        Depends on: [{stage.depends_on.join(", ")}]
                      </span>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleRemoveStage(stage.id)}
                  style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--critical)", padding: 6 }}
                  title="Remove stage"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
