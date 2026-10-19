import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { AuditEvent } from "../types";
import { Shield, Clock, User, FileText, CheckCircle2 } from "lucide-react";

export const AuditLogView: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAuditEvents();
  }, []);

  const loadAuditEvents = async () => {
    try {
      setLoading(true);
      const res = await api.listAudit(1, 50);
      setEvents(res.items);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Immutable Audit Trail</h1>
          <p className="page-description">
            Append-only governance record of all workflow analyses, simulations, policy evaluations, and reviewer decisions.
          </p>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div style={{ padding: 40, textAlign: "center", color: "var(--text-secondary)" }}>
            Loading audit records...
          </div>
        ) : events.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center" }}>
            <Shield size={36} color="var(--text-muted)" style={{ margin: "0 auto 12px" }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>No Audit Events Logged</h3>
            <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
              Actions such as running an analysis or logging a review decision will appear here.
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Target Entity</th>
                  <th>Audit Details</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id}>
                    <td style={{ fontFamily: "monospace", fontSize: 12, color: "var(--text-secondary)" }}>
                      {new Date(e.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <span style={{ display: "flex", alignItems: "center", gap: 5, fontWeight: 500 }}>
                        <User size={13} color="var(--text-muted)" /> {e.actor}
                      </span>
                    </td>
                    <td>
                      <span className="badge" style={{ backgroundColor: "#F1F5F9", color: "#334155" }}>
                        {e.action}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                        {e.entity_type}: <code style={{ fontSize: 11 }}>{e.entity_id ? e.entity_id.slice(0, 8) + "..." : "system"}</code>
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: "monospace", fontSize: 11, color: "var(--text-secondary)" }}>
                        {JSON.stringify(e.details)}
                      </span>
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
