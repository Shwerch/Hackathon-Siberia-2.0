import React, { useEffect, useState } from "react";
import { Code2, Download, PlusCircle } from "lucide-react";
import { createSession, formatUsd, sendTurn, SessionState } from "./api/client";
import { ChatPanel } from "./components/ChatPanel";
import { ResultTabs } from "./components/ResultTabs";
import { ExpertModal } from "./components/ExpertModal";

export function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<{
    text: string;
    answers?: Record<string, { choice?: string; other_text?: string }>;
  } | null>(null);
  const [expertOpen, setExpertOpen] = useState(false);

  const startNew = async () => {
    setError(null);
    try {
      const s = await createSession();
      setSession(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Бэкенд недоступен");
    }
  };

  useEffect(() => {
    startNew();
  }, []);

  const handleSend = async (
    text: string,
    answers?: Record<string, { choice?: string; other_text?: string }>
  ) => {
    if (!session) return;
    setLoading(true);
    setError(null);
    setLastPayload({ text, answers });
    try {
      const updated = await sendTurn(session.session_id, text, answers);
      setSession(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-slate-900">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-sm text-white">Ассистент «Синоникс»</span>
          {session && (
            <span className="text-xs text-slate-400">
              Расход сессии: {formatUsd(session.usage.evaluation_cost_usd)}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {session?.drawio_xml && (
            <a
              href={`/api/sessions/${session.session_id}/export/drawio`}
              download
              className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600/20 border border-amber-500/40 px-3 py-1.5 text-xs font-medium text-amber-300 hover:bg-amber-600/30"
            >
              <Download className="w-3.5 h-3.5" /> Скачать .drawio
            </a>
          )}
          {session && (
            <button
              type="button"
              onClick={() => setExpertOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700"
            >
              <Code2 className="w-3.5 h-3.5" /> Служебный JSON / Расходы
            </button>
          )}
          <button
            type="button"
            onClick={startNew}
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-teal-500"
          >
            <PlusCircle className="w-3.5 h-3.5" /> Новая сессия
          </button>
        </div>
      </header>

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-2 min-h-0">
        <ChatPanel
          session={session}
          loading={loading}
          error={error}
          onSend={handleSend}
          onRetry={() => (lastPayload ? handleSend(lastPayload.text, lastPayload.answers) : startNew())}
        />
        <ResultTabs session={session} />
      </main>

      {expertOpen && session && (
        <ExpertModal session={session} onClose={() => setExpertOpen(false)} />
      )}
    </div>
  );
}

export default App;
