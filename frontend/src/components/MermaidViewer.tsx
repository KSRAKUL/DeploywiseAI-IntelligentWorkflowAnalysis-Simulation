import React, { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { Download, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface MermaidViewerProps {
  id: string;
  chart: string;
}

export const MermaidViewer: React.FC<MermaidViewerProps> = ({ id, chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState<number>(1);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "loose",
      fontFamily: "Inter, sans-serif",
      flowchart: {
        curve: "basis",
        htmlLabels: true,
      },
    });

    const renderChart = async () => {
      if (!chart) return;
      try {
        setError(null);
        const uniqueId = `mermaid-${id}-${Math.random().toString(36).substring(2, 9)}`;
        // Pre-sanitize chart to fix unquoted labels or unescaped characters
        const safeChart = chart
          .split("\n")
          .map((line) => {
            const trimmed = line.trim();
            if (!trimmed || trimmed.startsWith("%%") || trimmed.startsWith("subgraph") || trimmed.startsWith("end") || trimmed.startsWith("classDef") || trimmed.includes("-->")) {
              return line;
            }
            const m = line.match(/^(\s*)([a-zA-Z0-9_-]+)\[([^"\]]+)\](:::.*)?$/);
            if (m) {
              const [, indent, nodeId, inner, cls = ""] = m;
              const cleaned = inner
                .replace(/\\n/g, "<br/>")
                .replace(/\n/g, "<br/>")
                .replace(/"/g, "'");
              return `${indent}${nodeId}["${cleaned}"]${cls}`;
            }
            return line;
          })
          .join("\n");

        const { svg } = await mermaid.render(uniqueId, safeChart);
        setSvgContent(svg);
      } catch (err: any) {
        console.error("Mermaid rendering failed:", err);
        setError("Diagram rendering fallback. Raw code available below.");
      }
    };

    renderChart();
  }, [id, chart]);

  const handleDownloadSvg = () => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${id}-workflow-architecture.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ background: "var(--card-bg, #ffffff)", border: "1px solid var(--border, #e2e8f0)", borderRadius: 8, padding: 16 }}>
      {/* Controls Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, paddingBottom: 8, borderBottom: "1px solid var(--border, #e2e8f0)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--text-secondary, #64748b)" }}>
          <span>Interactive Architecture Canvas</span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setZoom((z) => Math.min(z + 0.15, 2.0))}
            title="Zoom In"
            style={{ padding: "4px 8px" }}
          >
            <ZoomIn size={14} />
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setZoom((z) => Math.max(z - 0.15, 0.6))}
            title="Zoom Out"
            style={{ padding: "4px 8px" }}
          >
            <ZoomOut size={14} />
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setZoom(1)}
            title="Reset Zoom"
            style={{ padding: "4px 8px" }}
          >
            <RotateCcw size={14} />
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleDownloadSvg}
            title="Export as SVG"
            style={{ padding: "4px 10px", display: "flex", alignItems: "center", gap: 4 }}
          >
            <Download size={14} />
            <span>Export SVG</span>
          </button>
        </div>
      </div>

      {/* Render Area */}
      {error ? (
        <div style={{ padding: 16, background: "var(--bg, #f8fafc)", borderRadius: 6 }}>
          <p style={{ color: "var(--text-secondary, #64748b)", fontSize: 13, marginBottom: 8 }}>{error}</p>
          <pre style={{ fontSize: 11, background: "var(--card-bg, #ffffff)", padding: 8, borderRadius: 4, overflowX: "auto" }}>
            {chart}
          </pre>
        </div>
      ) : (
        <div
          ref={containerRef}
          style={{
            overflowX: "auto",
            overflowY: "hidden",
            padding: "16px 8px",
            display: "flex",
            justifyContent: "center",
            transform: `scale(${zoom})`,
            transformOrigin: "top center",
            transition: "transform 0.15s ease",
          }}
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />
      )}
    </div>
  );
};
