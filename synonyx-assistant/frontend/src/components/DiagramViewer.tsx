import React, { useMemo, useState } from "react";
import { Maximize2, ZoomIn, ZoomOut } from "lucide-react";

interface Props {
  drawioXml: string;
}

interface ParsedCell {
  id: string;
  value: string;
  style: string;
  vertex: boolean;
  edge: boolean;
  source?: string;
  target?: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

function getStyleProp(style: string, key: string, fallback = ""): string {
  const m = style.match(new RegExp(`${key}=([^;]+)`));
  return m ? m[1] : fallback;
}

function stripHtml(html: string): string {
  return html.replace(/<br\s*\/?>/gi, " · ").replace(/<[^>]+>/g, "").trim();
}

export const DiagramViewer: React.FC<Props> = ({ drawioXml }) => {
  const [zoom, setZoom] = useState(0.68);

  const parsed = useMemo(() => {
    if (!drawioXml) return null;
    const doc = new DOMParser().parseFromString(drawioXml, "text/xml");
    const model = doc.querySelector("mxGraphModel");
    const pageW = Number(model?.getAttribute("pageWidth") || 1450);
    const pageH = Number(model?.getAttribute("pageHeight") || 650);

    const cells: ParsedCell[] = [];
    const byId: Record<string, ParsedCell> = {};

    doc.querySelectorAll("mxCell").forEach((el) => {
      const id = el.getAttribute("id") || "";
      if (id === "0" || id === "1") return;
      const geo = el.querySelector("mxGeometry");
      const cell: ParsedCell = {
        id,
        value: el.getAttribute("value") || "",
        style: el.getAttribute("style") || "",
        vertex: el.getAttribute("vertex") === "1",
        edge: el.getAttribute("edge") === "1",
        source: el.getAttribute("source") || undefined,
        target: el.getAttribute("target") || undefined,
        x: Number(geo?.getAttribute("x") || 0),
        y: Number(geo?.getAttribute("y") || 0),
        w: Number(geo?.getAttribute("width") || 0),
        h: Number(geo?.getAttribute("height") || 0),
      };
      cells.push(cell);
      byId[id] = cell;
    });
    return { pageW, pageH, cells, byId };
  }, [drawioXml]);

  if (!parsed) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-slate-500">
        Схема появится после описания сетей и потоков.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#303E48]">
      <div className="flex items-center gap-2 p-2 bg-slate-900/90 border-b border-slate-800">
        <button
          type="button"
          onClick={() => setZoom((z) => Math.min(1.6, +(z + 0.15).toFixed(2)))}
          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
          title="Увеличить"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => setZoom((z) => Math.max(0.35, +(z - 0.15).toFixed(2)))}
          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
          title="Уменьшить"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => setZoom(0.68)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200"
        >
          <Maximize2 className="w-3.5 h-3.5" /> Вся схема
        </button>
        <span className="text-xs text-slate-400 ml-2">{Math.round(zoom * 100)}%</span>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <svg
          width={parsed.pageW * zoom}
          height={parsed.pageH * zoom}
          viewBox={`0 0 ${parsed.pageW} ${parsed.pageH}`}
          className="rounded-lg shadow-inner"
        >
          <rect width={parsed.pageW} height={parsed.pageH} fill="#303E48" />
          {parsed.cells
            .filter((c) => c.vertex)
            .map((c) => {
              const fill = getStyleProp(c.style, "fillColor", "none");
              const stroke = getStyleProp(c.style, "strokeColor", "none");
              const dashed = c.style.includes("dashed=1");
              const fontColor = getStyleProp(c.style, "fontColor", "#FFFFFF");
              const isTextOnly = c.style.startsWith("text;");
              const label = stripHtml(c.value);

              return (
                <g key={c.id}>
                  {!isTextOnly && (
                    <rect
                      x={c.x}
                      y={c.y}
                      width={c.w}
                      height={c.h}
                      rx={8}
                      fill={fill === "none" ? "transparent" : fill}
                      stroke={stroke === "none" ? "transparent" : stroke}
                      strokeWidth={2}
                      strokeDasharray={dashed ? "8 6" : undefined}
                    />
                  )}
                  {label && (
                    <text
                      x={c.x + (c.style.includes("align=center") ? c.w / 2 : 12)}
                      y={c.y + (c.style.includes("verticalAlign=top") ? 20 : c.h / 2 + 4)}
                      fill={fontColor}
                      fontSize={Number(getStyleProp(c.style, "fontSize", "12"))}
                      textAnchor={c.style.includes("align=center") ? "middle" : "start"}
                      fontFamily="Open Sans, sans-serif"
                    >
                      {label}
                    </text>
                  )}
                </g>
              );
            })}

          {parsed.cells
            .filter((c) => c.edge)
            .map((e) => {
              const src = e.source ? parsed.byId[e.source] : undefined;
              const tgt = e.target ? parsed.byId[e.target] : undefined;
              if (!src || !tgt) return null;
              const stroke = getStyleProp(e.style, "strokeColor", "#E06733");
              const x1 = src.x + src.w / 2;
              const y1 = src.y + src.h / 2;
              const x2 = tgt.x + tgt.w / 2;
              const y2 = tgt.y + tgt.h / 2;
              const midX = (x1 + x2) / 2;
              const midY = (y1 + y2) / 2;
              return (
                <g key={e.id}>
                  <path
                    d={`M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${y2} L ${x2} ${y2}`}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={2.2}
                  />
                  {e.value && (
                    <g>
                      <rect x={midX - 60} y={midY - 11} width={120} height={22} rx={11} fill="#354552" />
                      <text x={midX} y={midY + 4} fill="#FFFFFF" fontSize={10} textAnchor="middle">
                        {e.value}
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
        </svg>
      </div>
    </div>
  );
};
