import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { HealthStatus, PolicyConfig } from "../types";
import { ShieldCheck, Cpu, Key, CheckCircle, Info } from "lucide-react";

export const SettingsView: React.FC = () => {
  const [policy, setPolicy] = useState<PolicyConfig | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [geminiKey, setGeminiKey] = useState("");
  const [keySavedMessage, setKeySavedMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const [pol, hlt] = await Promise.all([api.getPolicy(), api.getHealth()]);
      setPolicy(pol);
      setHealth(hlt);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKey = () => {
    if (!geminiKey.trim()) return;
    localStorage.setItem("DEPLOYWISE_GEMINI_API_KEY", geminiKey.trim());
    setKeySavedMessage("Google Gemini API key saved locally! Ready for advisory reviewer calls.");
    setTimeout(() => setKeySavedMessage(null), 4000);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Policy & System Settings</h1>
          <p className="page-description">
            Inspect frozen scoring policy weights, deterministic rule definitions, and AI reviewer provider configuration.
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* System & LLM Status */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <Cpu size={18} color="var(--accent)" />
            <h2 style={{ fontSize: 16, fontWeight: 700 }}>AI Reviewer Engine Status</h2>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 13 }}>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ color: "var(--text-secondary)" }}>Active LLM Provider:</span>
              <span style={{ fontWeight: 600, fontFamily: "monospace" }}>{health?.llm.provider || "Multi-Model Engine"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ color: "var(--text-secondary)" }}>Provider Availability:</span>
              <span className="badge badge-pass">{health?.llm.status || "available"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <span style={{ color: "var(--text-secondary)" }}>Backend Version:</span>
              <span style={{ fontWeight: 600 }}>v{health?.version || "0.1.0"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
              <span style={{ color: "var(--text-secondary)" }}>Golden Rule Enforcement:</span>
              <span style={{ color: "var(--low)", fontWeight: 600 }}>Active (Strict Advisory Isolation)</span>
            </div>
          </div>

          {/* Google API Key Configuration */}
          <div style={{ marginTop: 20, paddingTop: 18, borderTop: "1px solid var(--border)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
              <Key size={15} color="var(--accent)" />
              <span>Google Gemini API Key (Optional)</span>
            </div>
            <p style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 10 }}>
              Whenever you wish to share your Google API key, enter it here or set <code>GEMINI_API_KEY</code> in <code>.env</code>.
            </p>

            {keySavedMessage && (
              <div style={{ padding: "6px 10px", background: "var(--low-bg)", color: "var(--low)", borderRadius: 4, marginBottom: 8, fontSize: 12 }}>
                {keySavedMessage}
              </div>
            )}

            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                style={{ flex: 1, padding: "7px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <button className="btn btn-primary btn-sm" onClick={handleSaveApiKey}>
                Save Key
              </button>
            </div>
          </div>
        </div>

        {/* Frozen Policy Inspection */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <ShieldCheck size={18} color="var(--accent)" />
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Frozen Policy v1.0.0</h2>
            </div>
            <span className="badge badge-pass" style={{ fontSize: 11 }}>100/100 Clean Pass Model</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Category Weights */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
                CATEGORY WEIGHTS (Sum = 100%)
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, fontSize: 12 }}>
                <div style={{ background: "var(--bg-app)", padding: 8, borderRadius: 4 }}>
                  <div style={{ color: "var(--text-secondary)" }}>Security</div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>25%</div>
                </div>
                <div style={{ background: "var(--bg-app)", padding: 8, borderRadius: 4 }}>
                  <div style={{ color: "var(--text-secondary)" }}>Testing</div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>25%</div>
                </div>
                <div style={{ background: "var(--bg-app)", padding: 8, borderRadius: 4 }}>
                  <div style={{ color: "var(--text-secondary)" }}>Recovery</div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>20%</div>
                </div>
                <div style={{ background: "var(--bg-app)", padding: 8, borderRadius: 4 }}>
                  <div style={{ color: "var(--text-secondary)" }}>Dependency</div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>15%</div>
                </div>
                <div style={{ background: "var(--bg-app)", padding: 8, borderRadius: 4 }}>
                  <div style={{ color: "var(--text-secondary)" }}>Governance</div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>15%</div>
                </div>
                <div style={{ background: "var(--bg-app)", padding: 8, borderRadius: 4 }}>
                  <div style={{ color: "var(--text-secondary)" }}>Category Cap</div>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>100 pts</div>
                </div>
              </div>
            </div>

            {/* Severity Penalty Points */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 6 }}>
                SEVERITY PENALTY DEDUCTIONS (Subtracted from 100)
              </div>
              <div style={{ display: "flex", gap: 10, fontSize: 12, flexWrap: "wrap" }}>
                <span className="badge badge-blocked">Critical: -50 pts</span>
                <span className="badge badge-high-risk">High: -30 pts</span>
                <span className="badge badge-needs-review">Medium: -15 pts</span>
                <span className="badge badge-pass">Low: -5 pts</span>
              </div>
            </div>

            {/* Verdict Thresholds (100/100 is Clean Pass) */}
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 8 }}>
                DELIVERY ASSURANCE VERDICT THRESHOLDS (100 / 100 = Clean Pass)
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: "var(--bg-app)", borderRadius: 4 }}>
                  <span className="badge badge-pass" style={{ minWidth: 90, textAlign: "center" }}>100 / 100</span>
                  <span style={{ fontWeight: 600, color: "var(--low)" }}>100% CLEAN PASS</span>
                  <span style={{ color: "var(--text-muted)" }}>— Zero risk deductions; pristine delivery pipeline</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: "var(--bg-app)", borderRadius: 4 }}>
                  <span className="badge badge-pass" style={{ minWidth: 90, textAlign: "center" }}>≥ 70 / 100</span>
                  <span style={{ fontWeight: 600, color: "var(--low)" }}>PASS</span>
                  <span style={{ color: "var(--text-muted)" }}>— Penalty points &lt; 30; delivery safe for release</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: "var(--bg-app)", borderRadius: 4 }}>
                  <span className="badge badge-needs-review" style={{ minWidth: 90, textAlign: "center" }}>40 – 69 / 100</span>
                  <span style={{ fontWeight: 600, color: "var(--medium)" }}>NEEDS_REVIEW</span>
                  <span style={{ color: "var(--text-muted)" }}>— Penalty points 30 – 59; non-critical governance checks failed</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: "var(--bg-app)", borderRadius: 4 }}>
                  <span className="badge badge-high-risk" style={{ minWidth: 90, textAlign: "center" }}>&lt; 40 / 100</span>
                  <span style={{ fontWeight: 600, color: "var(--high)" }}>HIGH_RISK</span>
                  <span style={{ color: "var(--text-muted)" }}>— Penalty points ≥ 60; significant risk across delivery pipeline</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: "var(--critical-bg)", borderRadius: 4 }}>
                  <span className="badge badge-blocked" style={{ minWidth: 90, textAlign: "center" }}>Any Blocker</span>
                  <span style={{ fontWeight: 600, color: "var(--critical)" }}>BLOCKED</span>
                  <span style={{ color: "var(--critical)" }}>— Mandatory safety gate failed (triggers release block regardless of score)</span>
                </div>
              </div>
            </div>

            <div style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg-app)", padding: 8, borderRadius: 4, lineHeight: 1.5 }}>
              💡 <strong>Human Psychology Standard:</strong> 100/100 represents a completely clean, zero-risk delivery pipeline. Deterministic policy violations deduct penalty points, lowering the score towards 0. Any blocking finding immediately halts production promotion.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
