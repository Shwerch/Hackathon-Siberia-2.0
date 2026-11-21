import React, { useEffect, useState } from "react";
import { X } from "lucide-react";
import { fetchResultJson, formatUsd, SessionState } from "../api/client";

interface Props {
  session: SessionState;
  onClose: () => void;
}

export const ExpertModal: React.FC<Props> = ({ session, onClose }) => {
  const [jsonText, setJsonText] = useState("");

  useEffect(() => {
    fetchResultJson(session.session_id)
      .then((d) => setJsonText(JSON.stringify(d, null, 2)))
      .catch(() => setJsonText("Ошибка загрузки служебного JSON"));
  }, [session.session_id]);

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl max-h-[85vh] flex flex-col rounded-xl border border-slate-700 bg-slate-900 text-slate-100">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <h3 className="text-sm font-semibold">Экспертная панель: расходы, логи и JSON</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
              <div className="text-slate-400">Входные токены</div>
              <div className="text-sm font-semibold mt-1">{session.usage.input_tokens}</div>
            </div>
            <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
              <div className="text-slate-400">Выходные токены</div>
              <div className="text-sm font-semibold mt-1">{session.usage.output_tokens}</div>
            </div>
            <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
              <div className="text-slate-400">Оценочная стоимость</div>
              <div className="text-sm font-semibold text-teal-400 mt-1">
                {formatUsd(session.usage.evaluation_cost_usd)}
              </div>
            </div>
            <div className="rounded-lg bg-slate-950 p-3 border border-slate-800">
              <div className="text-slate-400">Среднее время шага</div>
              <div className="text-sm font-semibold mt-1">
                {session.timing.mean_turn_seconds !== null ? `${session.timing.mean_turn_seconds} с` : "—"}
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <a
              href={`/api/sessions/${session.session_id}/export/logs?format=jsonl`}
              download={`logs_${session.session_id.slice(0, 8)}.jsonl`}
              className="rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-slate-200"
            >
              Выгрузить журнал (JSONL)
            </a>
            <a
              href={`/api/sessions/${session.session_id}/export/logs?format=csv`}
              download={`logs_${session.session_id.slice(0, 8)}.csv`}
              className="rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-slate-200"
            >
              Выгрузить журнал (CSV)
            </a>
          </div>

          <div>
            <div className="text-slate-400 mb-1 font-medium">Служебный JSON (schema_version 1.1):</div>
            <pre className="rounded-lg bg-slate-950 border border-slate-800 p-3 overflow-x-auto text-[11px] text-slate-300 max-h-72">
              {jsonText}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
