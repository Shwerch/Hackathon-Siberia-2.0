import React, { useState } from "react";
import { ClarifyQuestion } from "../api/client";

interface Props {
  questions: ClarifyQuestion[];
  disabled?: boolean;
  onSubmit: (answers: Record<string, { choice?: string; other_text?: string }>) => void;
}

export const ClarifyCard: React.FC<Props> = ({ questions, disabled, onSubmit }) => {
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [otherText, setOtherText] = useState<Record<string, string>>({});

  if (questions.length === 0) return null;

  const hasValidSelection = Object.entries(selected).some(([qid, val]) =>
    val === "__other__" ? Boolean(otherText[qid]?.trim()) : Boolean(val)
  );

  const handleSend = () => {
    const payload: Record<string, { choice?: string; other_text?: string }> = {};
    for (const q of questions) {
      const ch = selected[q.question_id];
      if (ch === "__other__") {
        const txt = (otherText[q.question_id] || "").trim();
        if (txt) payload[q.question_id] = { choice: "другое", other_text: txt };
      } else if (ch) {
        payload[q.question_id] = { choice: ch };
      }
    }
    onSubmit(payload);
  };

  return (
    <div className="mt-3 rounded-xl border border-amber-500/30 bg-slate-900 p-4 space-y-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-amber-400">
        Уточняющие вопросы
      </div>
      {questions.map((q) => (
        <div key={q.question_id} className="space-y-2">
          <div className="text-sm text-slate-200">{q.text}</div>
          <div className="flex flex-wrap gap-2">
            {q.options.map((opt) => {
              const active = selected[q.question_id] === opt.label;
              return (
                <button
                  key={opt.id}
                  type="button"
                  disabled={disabled}
                  onClick={() => setSelected((p) => ({ ...p, [q.question_id]: opt.label }))}
                  className={`rounded-lg px-3 py-1.5 text-xs border transition ${
                    active
                      ? "bg-teal-600 border-teal-500 text-white"
                      : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-500"
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
            {q.allow_unknown && (
              <button
                type="button"
                disabled={disabled}
                onClick={() => setSelected((p) => ({ ...p, [q.question_id]: "не знаю" }))}
                className={`rounded-lg px-3 py-1.5 text-xs border transition ${
                  selected[q.question_id] === "не знаю"
                    ? "bg-slate-600 border-slate-400 text-white"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                }`}
              >
                Не знаю
              </button>
            )}
            {q.allow_other && (
              <button
                type="button"
                disabled={disabled}
                onClick={() => setSelected((p) => ({ ...p, [q.question_id]: "__other__" }))}
                className={`rounded-lg px-3 py-1.5 text-xs border transition ${
                  selected[q.question_id] === "__other__"
                    ? "bg-amber-600 border-amber-500 text-white"
                    : "bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-500"
                }`}
              >
                Другое
              </button>
            )}
          </div>
          {selected[q.question_id] === "__other__" && (
            <input
              type="text"
              placeholder="Укажите ваш вариант..."
              value={otherText[q.question_id] || ""}
              onChange={(e) => setOtherText((p) => ({ ...p, [q.question_id]: e.target.value }))}
              className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-teal-500"
            />
          )}
        </div>
      ))}
      <button
        type="button"
        disabled={disabled || !hasValidSelection}
        onClick={handleSend}
        className="rounded-lg bg-teal-600 px-4 py-2 text-xs font-medium text-white hover:bg-teal-500 disabled:opacity-40"
      >
        Отправить ответы
      </button>
    </div>
  );
};
