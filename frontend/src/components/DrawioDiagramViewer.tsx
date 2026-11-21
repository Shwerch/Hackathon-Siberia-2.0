import React, { useMemo, useRef, useState } from 'react';

interface DrawioDiagramViewerProps {
  xml: string;
}

interface ParsedVertex {
  id: string;
  value: string;
  x: number;
  y: number;
  width: number;
  height: number;
  style: Record<string, string>;
}

interface ParsedEdge {
  id: string;
  value: string;
  source?: string;
  target?: string;
  sourcePoint?: { x: number; y: number };
  targetPoint?: { x: number; y: number };
  waypoints: Array<{ x: number; y: number }>;
  style: Record<string, string>;
}

function parseStyle(styleStr: string): Record<string, string> {
  const result: Record<string, string> = {};
  if (!styleStr) return result;
  styleStr.split(';').forEach((part) => {
    const trimmed = part.trim();
    if (!trimmed) return;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx === -1) {
      result[trimmed] = '1';
    } else {
      result[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
    }
  });
  return result;
}

function parseDrawioXml(xml: string): {
  vertices: ParsedVertex[];
  edges: ParsedEdge[];
  minX: number;
  minY: number;
  width: number;
  height: number;
  error?: string;
} {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xml, 'application/xml');
    const parseErr = doc.querySelector('parsererror');
    if (parseErr) {
      return {
        vertices: [],
        edges: [],
        minX: 0,
        minY: 0,
        width: 900,
        height: 550,
        error: 'Некорректный XML диаграммы'
      };
    }

    const cells = Array.from(doc.querySelectorAll('mxCell'));
    const vertexMap = new Map<string, ParsedVertex>();
    const vertices: ParsedVertex[] = [];
    const edges: ParsedEdge[] = [];

    for (const cell of cells) {
      const id = cell.getAttribute('id') || '';
      if (id === '0' || id === '1') continue;

      const isVertex = cell.getAttribute('vertex') === '1';
      const isEdge = cell.getAttribute('edge') === '1';
      const value = cell.getAttribute('value') || '';
      const style = parseStyle(cell.getAttribute('style') || '');
      const geom = cell.querySelector('mxGeometry');

      if (isVertex && geom) {
        const x = parseFloat(geom.getAttribute('x') || '0');
        const y = parseFloat(geom.getAttribute('y') || '0');
        const width = parseFloat(geom.getAttribute('width') || '120');
        const height = parseFloat(geom.getAttribute('height') || '60');
        const v: ParsedVertex = { id, value, x, y, width, height, style };
        vertexMap.set(id, v);
        vertices.push(v);
      } else if (isEdge) {
        const source = cell.getAttribute('source') || undefined;
        const target = cell.getAttribute('target') || undefined;
        let sourcePoint: { x: number; y: number } | undefined;
        let targetPoint: { x: number; y: number } | undefined;
        const waypoints: Array<{ x: number; y: number }> = [];

        if (geom) {
          const pts = Array.from(geom.querySelectorAll('mxPoint'));
          for (const pt of pts) {
            const px = parseFloat(pt.getAttribute('x') || '0');
            const py = parseFloat(pt.getAttribute('y') || '0');
            const asAttr = pt.getAttribute('as');
            if (asAttr === 'sourcePoint') {
              sourcePoint = { x: px, y: py };
            } else if (asAttr === 'targetPoint') {
              targetPoint = { x: px, y: py };
            } else {
              waypoints.push({ x: px, y: py });
            }
          }
        }
        edges.push({ id, value, source, target, sourcePoint, targetPoint, waypoints, style });
      }
    }

    // Resolve edge endpoints from connected vertices if points are omitted
    for (const e of edges) {
      if (!e.sourcePoint && e.source && vertexMap.has(e.source)) {
        const v = vertexMap.get(e.source)!;
        const exitX = e.style.exitX ? parseFloat(e.style.exitX) : 0.5;
        const exitY = e.style.exitY ? parseFloat(e.style.exitY) : 0.5;
        e.sourcePoint = { x: v.x + v.width * exitX, y: v.y + v.height * exitY };
      }
      if (!e.targetPoint && e.target && vertexMap.has(e.target)) {
        const v = vertexMap.get(e.target)!;
        const entryX = e.style.entryX ? parseFloat(e.style.entryX) : 0.5;
        const entryY = e.style.entryY ? parseFloat(e.style.entryY) : 0.5;
        e.targetPoint = { x: v.x + v.width * entryX, y: v.y + v.height * entryY };
      }
    }

    if (vertices.length === 0 && edges.length === 0) {
      return {
        vertices,
        edges,
        minX: 0,
        minY: 0,
        width: 1000,
        height: 600
      };
    }

    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    for (const v of vertices) {
      minX = Math.min(minX, v.x);
      minY = Math.min(minY, v.y);
      maxX = Math.max(maxX, v.x + v.width);
      maxY = Math.max(maxY, v.y + v.height);
    }
    for (const e of edges) {
      const pts = [
        ...(e.sourcePoint ? [e.sourcePoint] : []),
        ...e.waypoints,
        ...(e.targetPoint ? [e.targetPoint] : [])
      ];
      for (const p of pts) {
        minX = Math.min(minX, p.x);
        minY = Math.min(minY, p.y);
        maxX = Math.max(maxX, p.x);
        maxY = Math.max(maxY, p.y);
      }
    }

    const pad = 32;
    return {
      vertices,
      edges,
      minX: minX - pad,
      minY: minY - pad,
      width: Math.max(400, maxX - minX + pad * 2),
      height: Math.max(300, maxY - minY + pad * 2)
    };
  } catch {
    return {
      vertices: [],
      edges: [],
      minX: 0,
      minY: 0,
      width: 900,
      height: 550,
      error: 'Ошибка разбора XML схемы'
    };
  }
}

export const DrawioDiagramViewer: React.FC<DrawioDiagramViewerProps> = ({ xml }) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{ active: boolean; startX: number; startY: number }>({
    active: false,
    startX: 0,
    startY: 0
  });

  const parsed = useMemo(() => parseDrawioXml(xml), [xml]);

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    dragRef.current = {
      active: true,
      startX: e.clientX - pan.x,
      startY: e.clientY - pan.y
    };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragRef.current.active) return;
    setPan({
      x: e.clientX - dragRef.current.startX,
      y: e.clientY - dragRef.current.startY
    });
  };

  const handleMouseUp = () => {
    dragRef.current.active = false;
  };

  if (parsed.error) {
    return <div className="diagram-error">{parsed.error}</div>;
  }

  return (
    <div className="diagram-wrapper">
      <div className="diagram-toolbar">
        <div className="zoom-controls">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setZoom((z) => Math.max(0.4, +(z - 0.15).toFixed(2)))}
          >
            − Уменьшить
          </button>
          <span className="zoom-value">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => setZoom((z) => Math.min(2.5, +(z + 0.15).toFixed(2)))}
          >
            + Увеличить
          </button>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={handleResetView}
          >
            Показать целиком
          </button>
        </div>
        <span className="hint-text">Перетаскивайте схему мышью при увеличении</span>
      </div>

      <div
        className="diagram-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          width="100%"
          height="100%"
          viewBox={`${parsed.minX} ${parsed.minY} ${parsed.width} ${parsed.height}`}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center'
          }}
        >
          <defs>
            {['#E06733', '#35C4AF', '#FFAB4D', '#B9C5CD', '#6FA8DC', '#FFFFFF'].map(
              (color) => {
                const id = `arrow-${color.replace('#', '')}`;
                return (
                  <marker
                    key={id}
                    id={id}
                    viewBox="0 0 10 10"
                    refX="9"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 1 L 10 5 L 0 9 z" fill={color} />
                  </marker>
                );
              }
            )}
          </defs>

          <rect
            x={parsed.minX}
            y={parsed.minY}
            width={parsed.width}
            height={parsed.height}
            fill="#303E48"
          />

          {parsed.vertices.map((v) => {
            const fill =
              v.style.fillColor && v.style.fillColor !== 'none'
                ? v.style.fillColor
                : 'transparent';
            const stroke =
              v.style.strokeColor && v.style.strokeColor !== 'none'
                ? v.style.strokeColor
                : 'none';
            const strokeWidth = parseFloat(v.style.strokeWidth || '1.5');
            const isDashed = v.style.dashed === '1';
            const isHex = v.style.shape === 'hexagon';
            const isImage = v.style.shape === 'image' && v.style.image;

            const fontSize = parseFloat(v.style.fontSize || '12');
            const fontColor = v.style.fontColor || '#FFFFFF';
            const align = v.style.align || 'center';
            const vAlign = v.style.verticalAlign || 'middle';
            const rx = v.style.rounded === '1' ? 8 : 0;

            return (
              <g key={v.id}>
                {isImage ? (
                  <image
                    href={v.style.image}
                    x={v.x}
                    y={v.y}
                    width={v.width}
                    height={v.height}
                    preserveAspectRatio="xMidYMid meet"
                  />
                ) : isHex ? (
                  <polygon
                    points={`${v.x + 12},${v.y} ${v.x + v.width - 12},${v.y} ${
                      v.x + v.width
                    },${v.y + v.height / 2} ${v.x + v.width - 12},${
                      v.y + v.height
                    } ${v.x + 12},${v.y + v.height} ${v.x},${v.y + v.height / 2}`}
                    fill={fill}
                    stroke={stroke}
                    strokeWidth={strokeWidth}
                  />
                ) : (
                  v.style.text !== '1' && (
                    <rect
                      x={v.x}
                      y={v.y}
                      width={v.width}
                      height={v.height}
                      rx={rx}
                      fill={fill}
                      stroke={stroke}
                      strokeWidth={strokeWidth}
                      strokeDasharray={isDashed ? '8 6' : undefined}
                    />
                  )
                )}

                {v.value && (
                  <foreignObject
                    x={v.x + 6}
                    y={isImage ? v.y - 20 : v.y + 4}
                    width={Math.max(20, v.width - 12)}
                    height={isImage ? 20 : Math.max(20, v.height - 8)}
                    style={{ pointerEvents: 'none' }}
                  >
                    <div
                      style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent:
                          vAlign === 'top'
                            ? 'flex-start'
                            : vAlign === 'bottom'
                              ? 'flex-end'
                              : 'center',
                        textAlign:
                          align === 'left'
                            ? 'left'
                            : align === 'right'
                              ? 'right'
                              : 'center',
                        color: fontColor,
                        fontSize: `${fontSize}px`,
                        fontFamily: "'Open Sans', sans-serif",
                        fontWeight: v.style.fontStyle === '1' ? 700 : 400,
                        lineHeight: 1.3,
                        overflow: 'hidden',
                        wordBreak: 'break-word'
                      }}
                      dangerouslySetInnerHTML={{ __html: v.value }}
                    />
                  </foreignObject>
                )}
              </g>
            );
          })}

          {parsed.edges.map((e) => {
            const pts = [
              ...(e.sourcePoint ? [e.sourcePoint] : []),
              ...e.waypoints,
              ...(e.targetPoint ? [e.targetPoint] : [])
            ];
            if (pts.length < 2) return null;

            const stroke = e.style.strokeColor || '#E06733';
            const strokeWidth = parseFloat(e.style.strokeWidth || '2');
            const arrowId = `arrow-${stroke.replace('#', '')}`;
            const hasEnd = e.style.endArrow !== 'none';
            const hasStart = e.style.startArrow && e.style.startArrow !== 'none';
            const d = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

            const midIdx = Math.floor(pts.length / 2);
            const midA = pts[midIdx - 1];
            const midB = pts[midIdx];
            const labelX = (midA.x + midB.x) / 2;
            const labelY = (midA.y + midB.y) / 2;

            return (
              <g key={e.id}>
                <path
                  d={d}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                  markerEnd={hasEnd ? `url(#${arrowId})` : undefined}
                  markerStart={hasStart ? `url(#${arrowId})` : undefined}
                />
                {e.value && (
                  <g transform={`translate(${labelX}, ${labelY})`}>
                    <rect
                      x={-54}
                      y={-11}
                      width={108}
                      height={22}
                      rx={11}
                      fill="#354552"
                      stroke={stroke}
                      strokeWidth={1}
                    />
                    <text
                      x={0}
                      y={4}
                      textAnchor="middle"
                      fill="#FFFFFF"
                      fontSize="10"
                      fontWeight="700"
                      fontFamily="'Open Sans', sans-serif"
                    >
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
