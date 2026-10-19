import React, { useState } from "react";
import { Finding, Stage } from "../types";
import { Box, Layers, User, AlertCircle, ShieldAlert, CheckCircle, ArrowRight } from "lucide-react";

interface GraphCanvasProps {
  stages: Stage[];
  findings?: Finding[];
  selectedStageId?: string | null;
  onSelectStage?: (stageId: string) => void;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  stages,
  findings = [],
  selectedStageId,
  onSelectStage,
}) => {
  const [viewMode, setViewMode] = useState<"canvas" | "table">("canvas");

  // Determine stage warning/blocker states from findings
  const stageIssues = new Map<string, { blocked: boolean; warned: boolean; count: number }>();
  findings.forEach((f) => {
    f.stage_ids.forEach((sid) => {
      const current = stageIssues.get(sid) || { blocked: false, warned: false, count: 0 };
      if (f.blocking) current.blocked = true;
      else current.warned = true;
      current.count += 1;
      stageIssues.set(sid, current);
    });
  });

  // Calculate topological levels for canvas column layout
  const depthMap = new Map<string, number>();
  const calculateDepth = (stageId: string, visited = new Set<string>()): number => {
    if (depthMap.has(stageId)) return depthMap.get(stageId)!;
    if (visited.has(stageId)) return 0; // avoid cycle explosion
    visited.add(stageId);

    const stage = stages.find((s) => s.id === stageId);
    if (!stage || !stage.depends_on.length) {
      depthMap.set(stageId, 0);
      return 0;
    }

    const maxParent = Math.max(...stage.depends_on.map((p) => calculateDepth(p, new Set(visited))));
    const d = maxParent + 1;
    depthMap.set(stageId, d);
    return d;
  };

  stages.forEach((s) => calculateDepth(s.id));

  // Group stages by depth level
  const columns: Stage[][] = [];
  stages.forEach((s) => {
    const col = depthMap.get(s.id) || 0;
    while (columns.length <= col) columns.push([]);
    columns[col].push(s);
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Controls Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--text-secondary)" }}>
          <Layers size={16} />
          <span>Workflow Directed Acyclic Graph ({stages.length} stages)</span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button
            className={`btn btn-sm ${viewMode === "canvas" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setViewMode("canvas")}
          >
            Visual Canvas
          </button>
          <button
            className={`btn btn-sm ${viewMode === "table" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setViewMode("table")}
          >
            Accessible Table
          </button>
        </div>
      </div>

      {viewMode === "canvas" ? (
        <div className="canvas-container" style={{ padding: "32px 40px", display: "flex", gap: 48, minHeight: 380 }}>
          {columns.map((colStages, colIdx) => (
            <div
              key={colIdx}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 20,
                justifyContent: "center",
                position: "relative",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: -24,
                  fontSize: 11,
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  textTransform: "uppercase",
                }}
              >
                Layer {colIdx + 1}
              </div>

              {colStages.map((stage) => {
                const issue = stageIssues.get(stage.id);
                const isSelected = selectedStageId === stage.id;
                const isProd = stage.type === "deploy_production";

                return (
                  <div
                    key={stage.id}
                    className="graph-node"
                    onClick={() => onSelectStage?.(stage.id)}
                    style={{
                      borderLeft: issue?.blocked
                        ? "4px solid var(--critical)"
                        : issue?.warned
                        ? "4px solid var(--high)"
                        : isProd
                        ? "4px solid var(--accent)"
                        : "4px solid #CBD5E1",
                      backgroundColor: isSelected ? "var(--accent-subtle)" : "var(--surface)",
                      borderColor: isSelected ? "var(--accent)" : "var(--border)",
                      position: "relative",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
                        {stage.name}
                      </span>
                      {issue?.blocked ? (
                        <span title="Blocked by policy findings"><ShieldAlert size={16} color="var(--critical)" /></span>
                      ) : issue?.warned ? (
                        <span title="Risk findings present"><AlertCircle size={16} color="var(--high)" /></span>
                      ) : (
                        <CheckCircle size={15} color="var(--low)" />
                      )}
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--text-secondary)", marginBottom: 4 }}>
                      <Box size={12} />
                      <span style={{ fontFamily: "monospace" }}>{stage.type}</span>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, color: "var(--text-muted)" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                        <User size={11} /> {stage.owner || <em style={{ color: "var(--critical)" }}>Unowned</em>}
                      </span>
                      {stage.depends_on.length > 0 && (
                        <span style={{ fontSize: 10 }}>← {stage.depends_on.length} deps</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Stage ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Owner</th>
                <th>Dependencies</th>
                <th>Risk Status</th>
              </tr>
            </thead>
            <tbody>
              {stages.map((stage) => {
                const issue = stageIssues.get(stage.id);
                return (
                  <tr
                    key={stage.id}
                    onClick={() => onSelectStage?.(stage.id)}
                    style={{ cursor: "pointer", background: selectedStageId === stage.id ? "var(--accent-subtle)" : undefined }}
                  >
                    <td style={{ fontFamily: "monospace", fontWeight: 600 }}>{stage.id}</td>
                    <td>{stage.name}</td>
                    <td><span className="badge">{stage.type}</span></td>
                    <td>{stage.owner || <span style={{ color: "var(--critical)", fontWeight: 600 }}>Missing (Unowned)</span>}</td>
                    <td>{stage.depends_on.join(", ") || "—"}</td>
                    <td>
                      {issue?.blocked ? (
                        <span className="badge badge-blocked">Blocked</span>
                      ) : issue?.warned ? (
                        <span className="badge badge-high-risk">Warnings ({issue.count})</span>
                      ) : (
                        <span className="badge badge-pass">Clear</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
