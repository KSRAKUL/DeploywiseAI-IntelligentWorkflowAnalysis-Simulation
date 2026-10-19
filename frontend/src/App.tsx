import React, { useState } from "react";
import { AppShell } from "./components/AppShell";
import { OverviewView } from "./views/OverviewView";
import { WorkflowsView } from "./views/WorkflowsView";
import { WorkflowBuilderView } from "./views/WorkflowBuilderView";
import { AnalysisView } from "./views/AnalysisView";
import { ProjectAssessmentView } from "./views/ProjectAssessmentView";
import { WhatIfView } from "./views/WhatIfView";
import { ReportsView } from "./views/ReportsView";
import { AuditLogView } from "./views/AuditLogView";
import { SettingsView } from "./views/SettingsView";
import { api } from "./lib/api";

// Sample workflow JSON data for instant zero-friction testing
const SAMPLE_WORKFLOWS: Record<string, any> = {
  "01_bad_release.json": {
    name: "Bad Release — Missing Safety Gates",
    schema_version: "1.0",
    environment: "production",
    change_type: "standard",
    stages: [
      { id: "build", name: "Build Artifact", type: "build", owner: "platform-team", depends_on: [] },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: null, depends_on: ["build"] }
    ],
    metadata: { blast_radius: "high", dependencies_changed: false }
  },
  "02_improved_release.json": {
    name: "Improved Release — Complete Safety Gates",
    schema_version: "1.0",
    environment: "production",
    change_type: "standard",
    stages: [
      { id: "build", name: "Build Artifact", type: "build", owner: "platform-team", depends_on: [] },
      { id: "unit_test", name: "Unit Tests", type: "unit_test", owner: "qa-team", depends_on: ["build"] },
      { id: "security_scan", name: "Security Vulnerability Scan", type: "security_scan", owner: "sec-team", depends_on: ["unit_test"] },
      { id: "staging_deploy", name: "Deploy to Staging", type: "staging_deploy", owner: "deploy-team", depends_on: ["security_scan"] },
      { id: "staging_validation", name: "Staging Smoke & E2E Validation", type: "staging_validation", owner: "qa-team", depends_on: ["staging_deploy"] },
      { id: "approval", name: "Release Governance Approval", type: "approval", owner: "release-manager", depends_on: ["staging_validation"] },
      { id: "rollback_plan", name: "Canary Automated Rollback Plan", type: "rollback_plan", owner: "sre-team", depends_on: ["approval"] },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: "deploy-team", depends_on: ["rollback_plan"] },
      { id: "monitoring_check", name: "Post-Deploy Health Probe", type: "monitoring_check", owner: "sre-team", depends_on: ["deploy_production"] }
    ],
    metadata: { blast_radius: "low", dependencies_changed: false }
  },
  "03_missing_owner.json": {
    name: "Release Pipeline — Unowned Production Stage",
    schema_version: "1.0",
    environment: "production",
    change_type: "standard",
    stages: [
      { id: "build", name: "Build", type: "build", owner: "ci-team", depends_on: [] },
      { id: "unit_test", name: "Unit Tests", type: "unit_test", owner: "qa-team", depends_on: ["build"] },
      { id: "security_scan", name: "Security Scan", type: "security_scan", owner: "sec-team", depends_on: ["unit_test"] },
      { id: "approval", name: "Approval", type: "approval", owner: "manager", depends_on: ["security_scan"] },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: "", depends_on: ["approval"] }
    ],
    metadata: { blast_radius: "medium", dependencies_changed: false }
  },
  "04_skip_tests_on_fail.json": {
    name: "Pipeline with Bypassable Test Stage",
    schema_version: "1.0",
    environment: "production",
    change_type: "standard",
    stages: [
      { id: "build", name: "Build", type: "build", owner: "ci-team", depends_on: [] },
      { id: "unit_test", name: "Unit Tests (Skippable)", type: "unit_test", owner: "dev-team", depends_on: ["build"], continue_on_failure: true },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: "ops", depends_on: ["unit_test"] }
    ],
    metadata: { blast_radius: "medium", dependencies_changed: false }
  },
  "05_dependency_change.json": {
    name: "Dependency Upgrade Pipeline",
    schema_version: "1.0",
    environment: "production",
    change_type: "standard",
    stages: [
      { id: "build", name: "Build", type: "build", owner: "dev-team", depends_on: [] },
      { id: "unit_test", name: "Unit Tests", type: "unit_test", owner: "dev-team", depends_on: ["build"] },
      { id: "deploy_production", name: "Deploy to Production", type: "deploy_production", owner: "ops", depends_on: ["unit_test"] }
    ],
    metadata: { blast_radius: "high", dependencies_changed: true }
  }
};

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState("overview");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  // Stores the most recent full ProjectAssessmentResponse from GitHub/ZIP/CICD/Diagram ingestion
  const [lastAssessmentResult, setLastAssessmentResult] = useState<any>(null);

  const handleNavigate = (view: string, workflowId?: string) => {
    setCurrentView(view);
    if (workflowId) {
      setSelectedWorkflowId(workflowId);
    }
  };

  // Called by WorkflowsView after a successful project assessment
  const handleAssessmentComplete = (result: any) => {
    setLastAssessmentResult(result);
    setCurrentView("project-assessment");
    if (result?.workflow_id) {
      setSelectedWorkflowId(result.workflow_id);
    }
  };

  const handleLoadSample = async (sampleName: string) => {
    const sample = SAMPLE_WORKFLOWS[sampleName];
    if (!sample) return;

    try {
      const res = await api.createWorkflow(sample);
      setSelectedWorkflowId(res.workflow_id);
      setCurrentView("analysis");
    } catch (err: any) {
      alert(`Could not load sample: ${err.message}`);
    }
  };

  return (
    <AppShell currentView={currentView} onNavigate={handleNavigate}>
      {currentView === "overview" && (
        <OverviewView onNavigate={handleNavigate} onLoadSample={handleLoadSample} />
      )}
      {currentView === "workflows" && (
        <WorkflowsView
          onNavigate={handleNavigate}
          onLoadSample={handleLoadSample}
          onAssessmentComplete={handleAssessmentComplete}
        />
      )}
      {currentView === "builder" && (
        <WorkflowBuilderView onNavigate={handleNavigate} />
      )}
      {currentView === "analysis" && (
        <AnalysisView workflowId={selectedWorkflowId} onNavigate={handleNavigate} />
      )}
      {currentView === "project-assessment" && (
        <ProjectAssessmentView
          assessmentResult={lastAssessmentResult}
          onNavigate={handleNavigate}
        />
      )}
      {currentView === "what-if" && (
        <WhatIfView workflowId={selectedWorkflowId} onNavigate={handleNavigate} />
      )}
      {currentView === "reports" && <ReportsView />}
      {currentView === "audit" && <AuditLogView />}
      {currentView === "settings" && <SettingsView />}
    </AppShell>
  );
};
