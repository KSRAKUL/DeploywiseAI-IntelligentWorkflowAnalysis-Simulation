import React from "react";
import { Verdict } from "../types";
import { StatusBadge } from "./StatusBadge";

interface RiskScoreGaugeProps {
  score: number;
  verdict: Verdict;
  isBlocked: boolean;
  policyVersion?: string;
  ruleSetVersion?: string;
}

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({
  score,
  verdict,
  isBlocked,
  policyVersion = "1.0.0",
  ruleSetVersion = "1.0.0",
}) => {
  // Delivery Assurance Score: 100/100 is Clean Pass (Aligned with Human Psychology)
  const assuranceScore = Math.max(0, 100 - score);

  let color = "var(--low)";
  let bg = "var(--low-bg)";
  if (isBlocked || verdict === "BLOCKED") {
    color = "var(--critical)";
    bg = "var(--critical-bg)";
  } else if (assuranceScore < 50 || verdict === "HIGH_RISK") {
    color = "var(--high)";
    bg = "var(--high-bg)";
  } else if (assuranceScore < 80 || verdict === "NEEDS_REVIEW") {
    color = "var(--medium)";
    bg = "var(--medium-bg)";
  }

  return (
    <div className="card" style={{ display: "flex", alignItems: "center", gap: 24, padding: "20px 24px" }}>
      <div
        className="score-circle"
        style={{
          borderColor: color,
          color: color,
          backgroundColor: bg,
        }}
      >
        <span>{assuranceScore}</span>
        <span style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", marginTop: -4 }}>/ 100</span>
      </div>

      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
            Delivery Assurance Score:
          </span>
          <StatusBadge type="verdict" value={verdict} />
        </div>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.4 }}>
          {isBlocked ? (
            <span style={{ color: "var(--critical)", fontWeight: 600 }}>
              Deployment is blocked by mandatory policy rules regardless of score (Risk points deducted: {score}).
            </span>
          ) : assuranceScore === 100 ? (
            <span style={{ color: "var(--low)", fontWeight: 600 }}>
              100/100 Perfect Health — All deterministic safety gates and policies satisfied for release. Clean pipeline.
            </span>
          ) : assuranceScore >= 80 ? (
            <span>High delivery assurance ({assuranceScore}/100) — Minor operational checks failed ({score} risk deductions).</span>
          ) : assuranceScore >= 50 ? (
            <span>Review required — Non-critical governance or dependency checks failed ({score} risk deductions).</span>
          ) : (
            <span>Elevated delivery risk detected ({score} risk deductions). Remediation recommended before release.</span>
          )}
        </p>
        <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 11, color: "var(--text-muted)" }}>
          <span>Assurance Health: {assuranceScore}/100</span>
          <span>Risk Deductions: {score} pts</span>
          <span>Policy: v{policyVersion}</span>
          <span>Ruleset: v{ruleSetVersion}</span>
        </div>
      </div>
    </div>
  );
};
