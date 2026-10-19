import React from "react";
import {
  Shield,
  LayoutDashboard,
  GitBranch,
  PlayCircle,
  Sparkles,
  FileText,
  Clock,
  Settings,
  User,
  Plus,
} from "lucide-react";

interface AppShellProps {
  currentView: string;
  onNavigate: (view: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentView,
  onNavigate,
  children,
}) => {
  const navItems = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "workflows", label: "Assess Project", icon: GitBranch },
    { id: "project-assessment", label: "Assessment Results", icon: Shield },
    { id: "builder", label: "Workflow Builder", icon: Plus },
    { id: "analysis", label: "Risk Analysis", icon: PlayCircle },
    { id: "what-if", label: "What-If Simulation", icon: Sparkles },
    { id: "reports", label: "Reports & Export", icon: FileText },
    { id: "audit", label: "Audit Trail", icon: Clock },
    { id: "settings", label: "Policy & Settings", icon: Settings },
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <Shield size={22} />
            <span>Deploywise AI</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                className={`nav-item ${isActive ? "active" : ""}`}
                onClick={() => onNavigate(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 2 }}>
            Deploywise AI v0.1.0
          </div>
          <div>Contract: contracts-v1</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-content">
        <header className="top-bar">
          <div className="breadcrumbs">
            <span>Governance Console</span>
            <span>/</span>
            <span className="current" style={{ textTransform: "capitalize" }}>
              {currentView.replace("-", " ")}
            </span>
          </div>

          <div className="top-actions">
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--text-secondary)" }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: "var(--low)",
                }}
              />
              <span>Deterministic Core: Active</span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 12px",
                background: "var(--bg-app)",
                borderRadius: "var(--radius-sm)",
                fontSize: 13,
                fontWeight: 500,
                color: "var(--text-primary)",
              }}
            >
              <User size={15} color="var(--accent)" />
              <span>architect@company.com</span>
            </div>
          </div>
        </header>

        <main className="scroll-area">{children}</main>
      </div>
    </div>
  );
};
