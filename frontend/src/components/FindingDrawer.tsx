import React from "react";
import { Finding } from "../types";
import { StatusBadge } from "./StatusBadge";
import { X, ShieldAlert, CheckCircle2, AlertTriangle, ArrowRight, Lightbulb } from "lucide-react";

interface FindingDrawerProps {
  finding: Finding | null;
  onClose: () => void;
  onSimulateFix?: (finding: Finding) => void;
}

export const FindingDrawer: React.FC<FindingDrawerProps> = ({
  finding,
  onClose,
  onSimulateFix,
}) => {
  if (!finding) return null;

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {finding.source === "agent" ? (
              <Lightbulb size={20} color="var(--accent)" />
            ) : finding.blocking ? (
              <ShieldAlert size={20} color="var(--critical)" />
            ) : (
              <AlertTriangle size={20} color="var(--high)" />
            )}
            <div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ fontSize: 13, fontWeight: 700, fontFamily: "monospace" }}>
                  [{finding.rule_id}]
                </span>
                <StatusBadge type="severity" value={finding.severity} />
                <StatusBadge type="source" value={finding.source} />
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              color: "var(--text-secondary)",
            }}
          >
            <X size={20} />
          </button>
        </div>

        <div className="drawer-body">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>
            {finding.title}
          </h2>

          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* Stage Association */}
            <div style={{ background: "var(--bg-app)", padding: 12, borderRadius: "var(--radius-sm)" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }}>
                AFFECTED STAGES
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {finding.stage_ids.length > 0 ? (
                  finding.stage_ids.map((sid) => (
                    <span
                      key={sid}
                      style={{
                        background: "var(--surface)",
                        border: "1px solid var(--border)",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: 12,
                        fontFamily: "monospace",
                        color: "var(--text-primary)",
                      }}
                    >
                      {sid}
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Workflow-level / None</span>
                )}
              </div>
            </div>

            {/* Exact Evidence */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", color: "var(--text-secondary)", marginBottom: 6 }}>
                Exact Evidence
              </div>
              <div
                style={{
                  background: "#F8FAFD",
                  borderLeft: "3px solid var(--accent)",
                  padding: "10px 14px",
                  fontSize: 13,
                  lineHeight: 1.5,
                  color: "var(--text-primary)",
                  borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
                }}
              >
                {finding.evidence}
              </div>
            </div>

            {/* Why It Matters */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", color: "var(--text-secondary)", marginBottom: 6 }}>
                Why It Matters (Risk Analysis)
              </div>
              <p style={{ fontSize: 13, color: "var(--text-primary)", lineHeight: 1.5 }}>
                {finding.why_it_matters}
              </p>
            </div>

            {/* Recommended Fix */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", color: "var(--text-secondary)", marginBottom: 6 }}>
                Recommended Fix
              </div>
              <div
                style={{
                  background: "var(--low-bg)",
                  border: "1px solid var(--low-border)",
                  padding: "12px 14px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: 13,
                  color: "var(--text-primary)",
                  display: "flex",
                  gap: 10,
                }}
              >
                <CheckCircle2 size={18} color="var(--low)" style={{ flexShrink: 0, marginTop: 2 }} />
                <span>{finding.recommended_fix}</span>
              </div>
            </div>

            {/* Verification Criteria */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", color: "var(--text-secondary)", marginBottom: 6 }}>
                Verification Criteria
              </div>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, fontStyle: "italic" }}>
                "{finding.verification_criteria}"
              </p>
            </div>

            {/* Metadata Footer */}
            <div
              style={{
                marginTop: 12,
                paddingTop: 16,
                borderTop: "1px solid var(--border)",
                display: "flex",
                justifyContent: "space-between",
                fontSize: 12,
                color: "var(--text-muted)",
              }}
            >
              <span>Category: {finding.category}</span>
              <span>Rule Version: v{finding.rule_version}</span>
              <span>Confidence: {finding.confidence}</span>
            </div>
          </div>
        </div>

        {onSimulateFix && (
          <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={() => onSimulateFix(finding)}>
              Simulate Safer Graph in What-If <ArrowRight size={15} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
