import React, { useState } from "react";
import { RotateCcw, Send } from "lucide-react";
import { SessionState } from "../api/client";
import { WelcomeScreen } from "./WelcomeScreen";
import { ClarifyCard } from "./ClarifyCard";
import { MarkdownView } from "./MarkdownView";

interface Props {
  session: SessionState | null;
  loading: boolean;
  error: string | null;
  onSend: (text: string, answers?: Record<string, { choice?: string; other_text?: string }>) => void;
  onRetry: () => void;
}

export const ChatPanel: React.FC<Props> = ({ session, loading, error, onSend, onRetry }) => {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const txt = input.trim();
    setInput("");
    onSend(txt);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 border-r border-slate-800">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {(!session || session.messages.length === 0) && (
          <WelcomeScreen onUseExample={(txt) => setInput(txt)} />
        )}

        {session?.messages.map((m, idx) => (
          <div key={idx} className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}>
            <div
              className={`max-w-[92%] rounded-xl px-4 py-3 text-sm ${
                m.role === "user"
                  ? "bg-teal-700/30 border border-teal-600/40 text-slate-100 whitespace-pre-wrap"
                  : "bg-slate-900 border border-slate-800 text-slate-200"
              }`}
            >
              {m.role === "user" ? m.content : <MarkdownView content={m.content} />}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-800 flex flex-wrap gap-1.5">
                  {m.sources.map((s, si) => (
                    <span key={si} className="text-[11px] rounded bg-slate-800 px-2 py-0.5 text-slate-400">
                      {s.file} · {s.section}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {m.role === "assistant" &&
              idx === (session?.messages.length ?? 0) - 1 &&
              m.questions?.length > 0 && (
                <div className="w-full">
                  <ClarifyCard
                    questions={m.questions}
                    disabled={loading}
                    onSubmit={(ans) => onSend("Ответы на уточняющие вопросы", ans)}
                  />
                </div>
              )}
          </div>
        ))}

        {loading && (
          <div className="text-xs text-teal-400 animate-pulse">
            Анализирую потоки, проверяю правила «Синоникса» и строю схему...
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-950/30 p-3 flex items-center justify-between text-xs text-red-300">
            <span>{error}</span>
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex items-center gap-1 rounded bg-red-600/30 px-2.5 py-1 hover:bg-red-600/50"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Повторить
            </button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800 bg-slate-900/50 flex gap-2">
        <textarea
          rows={2}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Опишите сети, потоки данных/файлов или задайте вопрос по схеме..."
          className="flex-1 resize-none rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="self-end rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
