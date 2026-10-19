export type StageType =
  | "build"
  | "unit_test"
  | "integration_test"
  | "security_scan"
  | "secrets_scan"
  | "dependency_check"
  | "staging_deploy"
  | "staging_validation"
  | "approval"
  | "rollback_plan"
  | "deploy_production"
  | "monitoring_check"
  | "notify"
  | "custom";

export type Environment = "production" | "staging" | "development" | "test";
export type ChangeType = "standard" | "emergency" | "patch" | "major" | "minor";
export type BlastRadius = "high" | "medium" | "low";
export type Severity = "critical" | "high" | "medium" | "low";
export type Verdict = "PASS" | "NEEDS_REVIEW" | "HIGH_RISK" | "BLOCKED" | "INSUFFICIENT_EVIDENCE";
export type FindingSource = "rule" | "agent" | "scanner";
export type Category =
  | "security"
  | "testing"
  | "recovery"
  | "dependency"
  | "governance"
  | "maintainability"
  | "observability";

export interface Stage {
  id: string;
  name: string;
  type: StageType;
  owner?: string | null;
  depends_on: string[];
  continue_on_failure?: boolean;
  skippable?: boolean;
  exception_expiry?: string | null;
}

export interface WorkflowMetadata {
  blast_radius: BlastRadius;
  dependencies_changed: boolean;
}

export interface WorkflowInput {
  name: string;
  schema_version?: string;
  environment?: Environment;
  change_type?: ChangeType;
  stages: Stage[];
  metadata?: WorkflowMetadata;
}

export interface WorkflowSummary {
  workflow_id: string;
  name: string;
  environment: string;
  change_type: string;
  created_at: string;
}

export interface WorkflowVersion {
  version_id: string;
  version_number: number;
  is_draft: boolean;
  payload?: WorkflowInput;
  created_at: string;
}

export interface WorkflowDetail {
  workflow_id: string;
  name: string;
  environment: string;
  created_at: string;
  versions: WorkflowVersion[];
}

export interface Finding {
  finding_id: string;
  source: FindingSource;
  rule_id: string;
  rule_version: string;
  category: Category;
  severity: Severity;
  blocking: boolean;
  stage_ids: string[];
  title: string;
  evidence: string;
  why_it_matters: string;
  recommended_fix: string;
  verification_criteria: string;
  confidence: string;
  advisory: boolean;
  file_path?: string | null;
  line_number?: number | null;
  evidence_status?: string;
  impact?: string | null;
  suggested_patch?: string | null;
  tool_name?: string | null;
  remediation_status?: string;
}

export interface CategoryScore {
  category: Category;
  raw_score: number;
  weighted_score: number;
  weight: number;
  finding_count: number;
}

export interface AnalysisResult {
  analysis_id: string;
  workflow_id: string;
  workflow_version_id: string;
  policy_version: string;
  rule_set_version: string;
  status: string;
  score: number;
  assurance_score?: number;
  verdict: Verdict;
  is_blocked: boolean;
  category_scores: CategoryScore[];
  findings: Finding[];
  agent_run_ids?: string[];
  completed_at?: string;
}

export interface WhatIfOperation {
  operation: "add_stage" | "remove_stage" | "add_dependency" | "remove_dependency" | "update_stage";
  stage_id?: string;
  stage?: Stage;
  from_id?: string;
  to_id?: string;
  updates?: Record<string, any>;
}

export interface WhatIfResult {
  original_analysis: AnalysisResult;
  proposed_analysis: AnalysisResult;
  score_delta: number;
  assurance_score_delta?: number;
  verdict_change: boolean;
  resolved_findings: string[];
  still_present_findings: string[];
  new_findings: string[];
  graph_valid: boolean;
  graph_errors?: string[];
  simulation_id: string;
  original_diagram?: {
    mermaid_code: string;
    nodes: any[];
    edges: any[];
  } | null;
  proposed_diagram?: {
    mermaid_code: string;
    nodes: any[];
    edges: any[];
  } | null;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, any>;
}

export interface PolicyConfig {
  policy_version: string;
  rule_set_version: string;
  category_weights: Record<Category, number>;
  severity_points: Record<Severity, number>;
  category_cap: number;
  verdict_thresholds: {
    high_risk: number;
    review: number;
  };
}

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
  llm: {
    provider: string;
    status: string;
  };
  database: string;
}

export type AssessmentInputType = "github" | "zip" | "cicd" | "diagram" | "json";

export interface ProjectStructure {
  languages: string[];
  frameworks: string[];
  package_managers: string[];
  ci_workflows: string[];
  dockerfiles: string[];
  total_files: number;
  inspected_files: string[];
  commit_sha?: string | null;
  branch?: string | null;
}

export interface ScannerResult {
  scanner_name: string;
  category: Category;
  target: string;
  status: "passed" | "failed" | "skipped_not_installed" | "unsupported" | "timed_out";
  duration_ms: number;
  finding_count: number;
  error_message?: string | null;
}

export interface AssessmentCoverage {
  total_checks: number;
  executed_checks: number;
  passed_checks: number;
  failed_checks: number;
  skipped_checks: number;
  coverage_percentage: number;
}

export interface RemediationItem {
  priority: number;
  priority_label: string;
  finding_id: string;
  title: string;
  severity: Severity;
  category: Category;
  location?: string | null;
  recommended_fix: string;
  suggested_patch?: string | null;
  verification_criteria: string;
  effort_rationale: string;
}

export interface ProjectAssessmentResponse {
  assessment_id: string;
  project_name: string;
  input_type: AssessmentInputType;
  input_source: string;
  created_at: string;
  commit_sha?: string | null;
  workflow_id?: string | null;
  risk_score: number;
  coverage: AssessmentCoverage;
  verdict: Verdict;
  is_blocked: boolean;
  structure: ProjectStructure;
  scanner_results: ScannerResult[];
  findings: Finding[];
  category_scores: CategoryScore[];
  remediation_roadmap: RemediationItem[];
  ai_summary?: string | null;
}
