import React, { useState } from "react";
import { SessionState } from "../api/client";
import { DiagramViewer } from "./DiagramViewer";

interface Props {
  session: SessionState | null;
}

const STATUS_BADGE: Record<string, { label: string; cls: string }> = {
  completed: { label: "Проект готов", cls: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" },
  preliminary: { label: "Предварительная оценка", cls: "bg-amber-500/20 text-amber-300 border-amber-500/40" },
  needs_clarification: { label: "Требуются уточнения", cls: "bg-sky-500/20 text-sky-300 border-sky-500/40" },
  unsupported: { label: "Ограничение кейса", cls: "bg-red-500/20 text-red-300 border-red-500/40" },
};

export const ResultTabs: React.FC<Props> = ({ session }) => {
  const [tab, setTab] = useState<"diagram" | "rules" | "explanation">("diagram");

  if (!session) return null;
  const badge = STATUS_BADGE[session.status] || STATUS_BADGE.needs_clarification;

  return (
    <div className="flex flex-col h-full bg-slate-950">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-slate-900/60">
        <div className="flex gap-1">
          {[
            { id: "diagram", label: "Схема" },
            { id: "rules", label: `Правила (${session.rules_count})` },
            { id: "explanation", label: "Пояснение и БЗ" },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id as typeof tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                tab === t.id ? "bg-teal-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <span className={`text-xs px-2.5 py-0.5 rounded-full border ${badge.cls}`}>{badge.label}</span>
      </div>

      <div className="flex-1 overflow-auto">
        {tab === "diagram" && <DiagramViewer drawioXml={session.drawio_xml} />}

        {tab === "rules" && (
          <div className="p-4 space-y-4">
            {session.status === "preliminary" && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 text-xs text-amber-300">
                Предварительная оценка: минимум {session.rules_count} правил. Недостающие параметры:{" "}
                {session.unknowns.join("; ")}.
              </div>
            )}

            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-slate-400">
                  <tr>
                    <th className="p-2.5">№</th>
                    <th className="p-2.5">Тип</th>
                    <th className="p-2.5">Направление</th>
                    <th className="p-2.5">Режим</th>
                    <th className="p-2.5">Протокол / Порт</th>
                    <th className="p-2.5">Проверки</th>
                    <th className="p-2.5">Обоснование</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200">
                  {session.rules.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-900/40">
                      <td className="p-2.5 font-semibold">{r.id}</td>
                      <td className="p-2.5">{r.type === "data" ? "Данные" : "Файлы"}</td>
                      <td className="p-2.5">
                        {r.from} → {r.to}
                      </td>
                      <td className="p-2.5">{r.mode === "two-way" ? "Двунапр." : "Однонапр."}</td>
                      <td className="p-2.5">
                        {typeof r.protocol === "string"
                          ? `${r.protocol}${r.port ? ` :${r.port}` : ""}`
                          : Object.entries(r.protocol)
                              .map(([k, v]) => `${k}: ${v}`)
                              .join(" | ")}
                      </td>
                      <td className="p-2.5">{r.checks?.join(", ") || "—"}</td>
                      <td className="p-2.5">{r.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="text-xs text-slate-400">
              Пользователей передачи файлов:{" "}
              <span className="text-slate-200 font-medium">
                {session.file_users_count !== null
                  ? session.file_users_count
                  : `минимум ${session.file_users_range?.min ?? 1} (точное число не задано)`}
              </span>
            </div>
          </div>
        )}

        {tab === "explanation" && (
          <div className="p-4 space-y-4 text-sm text-slate-200 whitespace-pre-wrap">
            <div>{session.last_explanation || "Пояснение появится после анализа запроса."}</div>
            {session.requests_for_vendor.length > 0 && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 p-3 text-xs text-amber-200">
                <div className="font-semibold mb-1">Пожелания для разработчика продукта:</div>
                <ul className="list-disc pl-4 space-y-0.5">
                  {session.requests_for_vendor.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
