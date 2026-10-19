import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { WorkflowSummary } from "../types";
import {
  Upload,
  Plus,
  FileJson,
  AlertCircle,
  Play,
  Sparkles,
  GitBranch,
  FileArchive,
  Terminal,
  Image as ImageIcon,
  CheckCircle2,
  Loader2,
  ExternalLink,
} from "lucide-react";

interface WorkflowsViewProps {
  onNavigate: (view: string, workflowId?: string) => void;
  onLoadSample: (sampleName: string) => void;
  onAssessmentComplete?: (result: any) => void;
}

type IntakeTab = "github" | "zip" | "cicd" | "diagram" | "json";

export const WorkflowsView: React.FC<WorkflowsViewProps> = ({ onNavigate, onLoadSample, onAssessmentComplete }) => {
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Intake State
  const [activeTab, setActiveTab] = useState<IntakeTab>("github");
  const [submitting, setSubmitting] = useState(false);
  const [intakeError, setIntakeError] = useState<string | null>(null);
  const [intakeSuccess, setIntakeSuccess] = useState<string | null>(null);

  // GitHub Form
  const [githubUrl, setGithubUrl] = useState("");
  const [githubBranch, setGithubBranch] = useState("");

  // ZIP Form
  const [zipFile, setZipFile] = useState<File | null>(null);

  // CI/CD Form
  const [cicdContent, setCicdContent] = useState("");
  const [cicdFilename, setCicdFilename] = useState("deploy.yml");

  // Diagram Form
  const [diagramFile, setDiagramFile] = useState<File | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const res = await api.listWorkflows(1, 50);
      setWorkflows(res.items);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGitHubSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl.trim()) {
      setIntakeError("Please provide a valid GitHub repository URL.");
      return;
    }

    try {
      setSubmitting(true);
      setIntakeError(null);
      setIntakeSuccess("Cloning repository, discovering architecture, and running security scanners...");
      const res = await api.assessGitHub(githubUrl.trim(), githubBranch.trim() || undefined);
      setIntakeSuccess(`Assessment completed for ${res.project_name}! Redirecting to results...`);
      await loadWorkflows();
      if (onAssessmentComplete) {
        onAssessmentComplete(res);
      } else if (res.workflow_id) {
        onNavigate("analysis", res.workflow_id);
      }
    } catch (err: any) {
      setIntakeError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleZipSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!zipFile) {
      setIntakeError("Please select a .zip archive to upload.");
      return;
    }

    try {
      setSubmitting(true);
      setIntakeError(null);
      setIntakeSuccess("Extracting archive safely, inspecting files, and running static scanners...");
      const res = await api.assessZip(zipFile);
      setIntakeSuccess(`Assessment completed for ${res.project_name}! Redirecting to results...`);
      await loadWorkflows();
      if (onAssessmentComplete) {
        onAssessmentComplete(res);
      } else if (res.workflow_id) {
        onNavigate("analysis", res.workflow_id);
      }
    } catch (err: any) {
      setIntakeError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCicdSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cicdContent.trim()) {
      setIntakeError("Please paste your GitHub Actions or GitLab CI YAML content.");
      return;
    }

    try {
      setSubmitting(true);
      setIntakeError(null);
      setIntakeSuccess("Parsing workflow DAG, checking topology, and evaluating release gates...");
      const res = await api.assessCicd(cicdContent.trim(), cicdFilename.trim() || "workflow.yml");
      setIntakeSuccess(`Assessment completed! Redirecting to results...`);
      await loadWorkflows();
      if (onAssessmentComplete) {
        onAssessmentComplete(res);
      } else if (res.workflow_id) {
        onNavigate("analysis", res.workflow_id);
      }
    } catch (err: any) {
      setIntakeError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDiagramSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!diagramFile) {
      setIntakeError("Please upload an architecture or workflow diagram image.");
      return;
    }

    try {
      setSubmitting(true);
      setIntakeError(null);
      setIntakeSuccess("Extracting workflow stages and dependencies from diagram...");
      const res = await api.assessDiagram(diagramFile);
      setIntakeSuccess(`Diagram analysis completed! Redirecting to results...`);
      await loadWorkflows();
      if (onAssessmentComplete) {
        onAssessmentComplete(res);
      } else if (res.workflow_id) {
        onNavigate("analysis", res.workflow_id);
      }
    } catch (err: any) {
      setIntakeError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleJsonFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 256 * 1024) {
      setIntakeError("JSON file exceeds maximum allowable size of 256 KB.");
      return;
    }

    try {
      setSubmitting(true);
      setIntakeError(null);
      const res = await api.importWorkflow(file);
      await loadWorkflows();
      onNavigate("analysis", res.workflow_id);
    } catch (err: any) {
      setIntakeError(err.message);
    } finally {
      setSubmitting(false);
      e.target.value = "";
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Project & Workflow Assurance</h1>
          <p className="page-description">
            Submit a real software project or delivery pipeline to discover control gaps, scan for security flaws, and evaluate production readiness.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-secondary" onClick={() => onNavigate("builder")}>
            <Plus size={16} /> Visual Workflow Builder
          </button>
        </div>
      </div>

      {/* Unified Project Ingestion Card */}
      <div className="card" style={{ marginBottom: 24, padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700 }}>Submit Project for Full-Spectrum Assessment</h2>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--border)", paddingBottom: 12, marginBottom: 20, overflowX: "auto" }}>
          <button
            className={`btn btn-sm ${activeTab === "github" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => { setActiveTab("github"); setIntakeError(null); }}
          >
            <GitBranch size={14} /> 1. GitHub Repository
          </button>
          <button
            className={`btn btn-sm ${activeTab === "zip" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => { setActiveTab("zip"); setIntakeError(null); }}
          >
            <FileArchive size={14} /> 2. ZIP Source Archive
          </button>
          <button
            className={`btn btn-sm ${activeTab === "cicd" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => { setActiveTab("cicd"); setIntakeError(null); }}
          >
            <Terminal size={14} /> 3. CI/CD Pipeline (YAML)
          </button>
          <button
            className={`btn btn-sm ${activeTab === "diagram" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => { setActiveTab("diagram"); setIntakeError(null); }}
          >
            <ImageIcon size={14} /> 4. Architecture Diagram
          </button>
          <button
            className={`btn btn-sm ${activeTab === "json" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => { setActiveTab("json"); setIntakeError(null); }}
          >
            <FileJson size={14} /> 5. JSON Specification
          </button>
        </div>

        {/* Feedback Alerts */}
        {intakeError && (
          <div
            style={{
              backgroundColor: "var(--critical-bg)",
              border: "1px solid var(--critical-border)",
              color: "var(--critical)",
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontSize: 13,
            }}
          >
            <AlertCircle size={18} />
            <span>{intakeError}</span>
          </div>
        )}

        {intakeSuccess && (
          <div
            style={{
              backgroundColor: "rgba(37, 99, 235, 0.1)",
              border: "1px solid var(--accent)",
              color: "var(--accent)",
              padding: "10px 14px",
              borderRadius: "var(--radius-sm)",
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 10,
              fontSize: 13,
            }}
          >
            {submitting ? <Loader2 size={18} className="spin" /> : <CheckCircle2 size={18} />}
            <span>{intakeSuccess}</span>
          </div>
        )}

        {/* Tab 1: GitHub Form */}
        {activeTab === "github" && (
          <form onSubmit={handleGitHubSubmit}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 12, alignItems: "flex-end" }}>
              <div>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
                  Git / GitHub Repository URL (HTTPS)
                </label>
                <input
                  type="text"
                  placeholder="https://github.com/owner/repository"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  disabled={submitting}
                  style={{
                    width: "100%",
                    padding: "9px 12px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-main)",
                    color: "var(--text-primary)",
                    fontSize: 13,
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
                  Branch / Tag (Optional)
                </label>
                <input
                  type="text"
                  placeholder="main"
                  value={githubBranch}
                  onChange={(e) => setGithubBranch(e.target.value)}
                  disabled={submitting}
                  style={{
                    width: "140px",
                    padding: "9px 12px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--border)",
                    backgroundColor: "var(--bg-main)",
                    color: "var(--text-primary)",
                    fontSize: 13,
                  }}
                />
              </div>
              <button type="submit" className="btn btn-primary" disabled={submitting} style={{ padding: "9px 20px" }}>
                {submitting ? <Loader2 size={15} className="spin" /> : <Play size={15} />}
                {submitting ? "Analyzing..." : "Assess Repository"}
              </button>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
              * Shallow clones repository safely, pins commit SHA, discovers CI/CD workflows, and executes security & dependency scanners.
            </div>
          </form>
        )}

        {/* Tab 2: ZIP Form */}
        {activeTab === "zip" && (
          <form onSubmit={handleZipSubmit}>
            <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                disabled={submitting}
                style={{ fontSize: 13 }}
              />
              <button type="submit" className="btn btn-primary" disabled={submitting || !zipFile}>
                {submitting ? <Loader2 size={15} className="spin" /> : <Upload size={15} />}
                {submitting ? "Processing..." : "Assess Source Code ZIP"}
              </button>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
              * Enforces strict Zip-Slip defenses, size limits (50 MB), and scans for unpinned dependencies, secrets, and container risks.
            </div>
          </form>
        )}

        {/* Tab 3: CI/CD YAML Form */}
        {activeTab === "cicd" && (
          <form onSubmit={handleCicdSubmit}>
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
                Paste GitHub Actions or GitLab CI Workflow YAML
              </label>
              <textarea
                rows={6}
                placeholder="name: Delivery Pipeline&#10;on: [push]&#10;jobs:&#10;  test:&#10;    runs-on: ubuntu-latest&#10;    steps:&#10;      - run: npm test"
                value={cicdContent}
                onChange={(e) => setCicdContent(e.target.value)}
                disabled={submitting}
                style={{
                  width: "100%",
                  padding: "10px",
                  fontFamily: "monospace",
                  fontSize: 12,
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)",
                  backgroundColor: "var(--bg-main)",
                  color: "var(--text-primary)",
                }}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <input
                type="text"
                placeholder="workflow.yml"
                value={cicdFilename}
                onChange={(e) => setCicdFilename(e.target.value)}
                style={{
                  width: "180px",
                  padding: "6px 10px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)",
                  fontSize: 12,
                }}
              />
              <button type="submit" className="btn btn-primary" disabled={submitting || !cicdContent.trim()}>
                {submitting ? <Loader2 size={15} className="spin" /> : <Play size={15} />}
                {submitting ? "Analyzing..." : "Assess CI/CD Pipeline"}
              </button>
            </div>
          </form>
        )}

        {/* Tab 4: Diagram & Technical Report Form */}
        {activeTab === "diagram" && (
          <form onSubmit={handleDiagramSubmit}>
            <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp,image/svg+xml,.svg,.pdf"
                onChange={(e) => setDiagramFile(e.target.files?.[0] || null)}
                disabled={submitting}
                style={{ fontSize: 13 }}
              />
              <button type="submit" className="btn btn-primary" disabled={submitting || !diagramFile}>
                {submitting ? <Loader2 size={15} className="spin" /> : <ImageIcon size={15} />}
                {submitting ? "Analyzing..." : "Assess Diagram / PDF Report"}
              </button>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
              * Supports architecture screenshots, pipeline diagrams (PNG, JPEG, SVG), and technical PDF design documents. Automatically reconstructs the workflow and generates an improved, corrected delivery diagram.
            </div>
          </form>
        )}

        {/* Tab 5: JSON Form */}
        {activeTab === "json" && (
          <div>
            <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
              <label className="btn btn-secondary" style={{ cursor: "pointer" }}>
                <Upload size={15} /> Upload Deploywise JSON
                <input
                  type="file"
                  accept=".json,application/json"
                  onChange={handleJsonFileUpload}
                  style={{ display: "none" }}
                  disabled={submitting}
                />
              </label>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>or seed with a pre-configured scenario:</span>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn btn-secondary btn-sm" onClick={() => onLoadSample("01_bad_release.json")}>
                01 Bad Release (No Tests/Scan)
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => onLoadSample("02_improved_release.json")}>
                02 Improved Release
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => onLoadSample("03_missing_owner.json")}>
                03 Missing Owner
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => onLoadSample("04_skip_tests_on_fail.json")}>
                04 Skip Tests on Fail
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => onLoadSample("05_dependency_change.json")}>
                05 Dependency Change
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Workflows List Table */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700 }}>Assessed Workflows & Pipelines ({workflows.length})</h2>
        </div>

        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)" }}>
            Loading workflows...
          </div>
        ) : workflows.length === 0 ? (
          <div style={{ padding: 48, textAlign: "center" }}>
            <FileJson size={40} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>No Assessed Workflows Found</h3>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 16 }}>
              Submit a GitHub repository URL, upload a project ZIP, or choose a sample scenario above to get started.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Workflow / Project Name</th>
                  <th>ID</th>
                  <th>Target Environment</th>
                  <th>Change Type</th>
                  <th>Assessed At</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((wf) => (
                  <tr key={wf.workflow_id}>
                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{wf.name}</td>
                    <td style={{ fontFamily: "monospace", fontSize: 12, color: "var(--text-muted)" }}>
                      {wf.workflow_id.slice(0, 8)}...
                    </td>
                    <td>
                      <span className="badge">{wf.environment}</span>
                    </td>
                    <td>{wf.change_type}</td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {new Date(wf.created_at).toLocaleString()}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: 8 }}>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onNavigate("analysis", wf.workflow_id)}
                        >
                          <Play size={13} /> View Assessment
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => onNavigate("what-if", wf.workflow_id)}
                        >
                          <Sparkles size={13} /> What-If
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
