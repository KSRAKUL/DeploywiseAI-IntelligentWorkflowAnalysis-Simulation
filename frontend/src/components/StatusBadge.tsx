import React from "react";
import { FindingSource, Severity, Verdict } from "../types";

interface StatusBadgeProps {
  type: "verdict" | "severity" | "source";
  value: Verdict | Severity | FindingSource;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, label }) => {
  if (type === "verdict") {
    switch (value) {
      case "BLOCKED":
        return <span className="badge badge-blocked">⛔ BLOCKED</span>;
      case "HIGH_RISK":
        return <span className="badge badge-high-risk">⚠️ HIGH RISK</span>;
      case "NEEDS_REVIEW":
        return <span className="badge badge-needs-review">🔍 NEEDS REVIEW</span>;
      case "PASS":
        return <span className="badge badge-pass">✅ PASS</span>;
      case "INSUFFICIENT_EVIDENCE":
        return <span className="badge badge-needs-review">⚠️ INSUFFICIENT EVIDENCE</span>;
      default:
        return <span className="badge">{value}</span>;
    }
  }

  if (type === "severity") {
    switch (value) {
      case "critical":
        return <span className="badge badge-blocked">Critical</span>;
      case "high":
        return <span className="badge badge-high-risk">High</span>;
      case "medium":
        return <span className="badge badge-needs-review">Medium</span>;
      case "low":
        return <span className="badge badge-pass">Low</span>;
      default:
        return <span className="badge">{value}</span>;
    }
  }

  if (type === "source") {
    if (value === "agent") {
      return <span className="badge badge-advisory">💡 Advisory Agent</span>;
    }
    if (value === "scanner") {
      return <span className="badge badge-high-risk">🔍 Security Scanner</span>;
    }
    return <span className="badge badge-rule">🛡️ Deterministic Rule</span>;
  }

  return <span className="badge">{label || value}</span>;
};
