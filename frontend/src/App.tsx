import React, { useCallback, useEffect, useState } from 'react';
import {
  createSession,
  downloadDrawio,
  downloadLogs,
  getExportJson,
  getModelsMeta,
  getSession,
  getVendorRequests,
  sendMessage
} from './api/client';
import {
  ChatMessage,
  ModelsMetaResponse,
  ProjectResult,
  QuestionAnswerPayload,
  SendMessageRequest,
  SessionStatus,
  TelemetryInfo,
  VendorRequestItem
} from './types/api';
import { generateUuid } from './utils/formatters';
import { Header } from './components/Header';
import { StartScreen } from './components/StartScreen';
import { ChatPanel } from './components/ChatPanel';
import { ResultPanel } from './components/ResultPanel';
import {
  CostModal,
  JsonModal,
  ModelsMetaModal,
  VendorRequestsModal
} from './components/Modals';

const STORAGE_KEY = 'synonyx_active_session_id';

const EMPTY_TELEMETRY: TelemetryInfo = {
  usage_status: 'confirmed',
  total_cost_usd: 0,
  total_input_tokens: 0,
  total_output_tokens: 0,
  models_breakdown: []
};

export const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<SessionStatus>('needs_clarification');
  const [welcomeMessage, setWelcomeMessage] = useState(
    'Я помогу определить, где в вашей инфраструктуре разместить «Синоникс» и межсетевой экран, а также посчитаю минимальное количество правил передачи данных и файлов.'
  );
  const [examplePrompt, setExamplePrompt] = useState(
    'Есть закрытая сеть цеха и офисная сеть. Два сервера цеха отправляют журналы на сервер в офисе по UDP 514. Сервер в офисе опрашивает контроллер по Modbus TCP. Инженер из офиса передаёт в цех файлы программ для станков, их нужно проверять антивирусом.'
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [result, setResult] = useState<ProjectResult | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryInfo>(EMPTY_TELEMETRY);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<SendMessageRequest | null>(null);

  const [showCostModal, setShowCostModal] = useState(false);
  const [jsonModalData, setJsonModalData] = useState<unknown | null>(null);
  const [vendorItems, setVendorItems] = useState<VendorRequestItem[] | null>(null);
  const [modelsMeta, setModelsMeta] = useState<ModelsMetaResponse | null>(null);
  const [showModelsModal, setShowModelsModal] = useState(false);

  const startFreshSession = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await createSession();
      localStorage.setItem(STORAGE_KEY, data.session_id);
      setSessionId(data.session_id);
      setStatus(data.status);
      if (data.welcome_message) setWelcomeMessage(data.welcome_message);
      if (data.example_prompt) setExamplePrompt(data.example_prompt);
      setMessages([]);
      setResult(null);
      setTelemetry(data.telemetry ?? EMPTY_TELEMETRY);
      setLastPayload(null);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Не удалось создать новую сессию'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const savedId = localStorage.getItem(STORAGE_KEY);
    if (savedId) {
      getSession(savedId)
        .then((state) => {
          setSessionId(state.session_id);
          setStatus(state.status);
          if (state.welcome_message) setWelcomeMessage(state.welcome_message);
          if (state.example_prompt) setExamplePrompt(state.example_prompt);
          setMessages(state.messages || []);
          setResult(state.result);
          setTelemetry(state.telemetry ?? EMPTY_TELEMETRY);
        })
        .catch(() => {
          void startFreshSession();
        });
    } else {
      void startFreshSession();
    }
  }, [startFreshSession]);

  const executeStep = async (
    payload: SendMessageRequest,
    userDisplayText: string,
    appendUserBubble: boolean
  ) => {
    if (!sessionId) return;
    setLoading(true);
    setErrorMessage(null);
    setLastPayload(payload);

    if (appendUserBubble && userDisplayText) {
      setMessages((prev) => [
        ...prev,
        {
          id: generateUuid(),
          role: 'user',
          text: userDisplayText,
          timestamp: new Date().toISOString()
        }
      ]);
    }

    try {
      const res = await sendMessage(sessionId, payload);
      setStatus(res.status);
      setTelemetry(res.telemetry);
      if (res.result) {
        setResult(res.result);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: generateUuid(),
          role: 'assistant',
          text: res.assistant_message.text,
          sources: res.assistant_message.sources,
          clarification_questions: res.assistant_message.clarification_questions,
          timestamp: new Date().toISOString()
        }
      ]);
      setLastPayload(null);
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Ошибка при обращении к серверу. Попробуйте повторить запрос.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSendText = (text: string) => {
    const payload: SendMessageRequest = {
      client_request_id: generateUuid(),
      text,
      answers: []
    };
    void executeStep(payload, text, true);
  };

  const handleSendAnswers = (answers: QuestionAnswerPayload[], extraText: string) => {
    const summaryParts = answers.map((a) => {
      if (a.is_unknown) return 'Не знаю';
      if (a.other_text) return `Другое: ${a.other_text}`;
      return a.selected_options.join(', ');
    });
    const display = extraText
      ? `${summaryParts.join(' | ')}\n${extraText}`
      : `Уточнение: ${summaryParts.join(' | ')}`;

    const payload: SendMessageRequest = {
      client_request_id: generateUuid(),
      text: extraText,
      answers
    };
    void executeStep(payload, display, true);
  };

  const handleRetry = () => {
    if (!lastPayload) {
      void startFreshSession();
      return;
    }
    void executeStep(lastPayload, '', false);
  };

  const handleOpenJsonModal = async () => {
    if (!sessionId) return;
    try {
      const data = await getExportJson(sessionId);
      setJsonModalData(data);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Не удалось загрузить служебный JSON'
      );
    }
  };

  const handleOpenVendorModal = async () => {
    if (!sessionId) return;
    try {
      const items = await getVendorRequests(sessionId);
      setVendorItems(items);
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Не удалось загрузить пожелания'
      );
    }
  };

  const handleOpenModelsModal = async () => {
    setShowModelsModal(true);
    try {
      const meta = await getModelsMeta();
      setModelsMeta(meta);
    } catch {
      // keep modal open with error/empty state
    }
  };

  return (
    <div className="app-shell">
      <Header
        sessionId={sessionId}
        status={status}
        telemetry={telemetry}
        hasResult={Boolean(result)}
        onNewSession={() => void startFreshSession()}
        onOpenCostModal={() => setShowCostModal(true)}
        onOpenJsonModal={() => void handleOpenJsonModal()}
        onDownloadLogs={(fmt) => sessionId && void downloadLogs(sessionId, fmt)}
        onOpenVendorModal={() => void handleOpenVendorModal()}
        onOpenModelsModal={() => void handleOpenModelsModal()}
      />

      {messages.length === 0 ? (
        <StartScreen
          welcomeMessage={welcomeMessage}
          examplePrompt={examplePrompt}
          loading={loading}
          errorMessage={errorMessage}
          onSend={handleSendText}
          onRetry={handleRetry}
        />
      ) : (
        <main className="workspace-split">
          <ChatPanel
            messages={messages}
            loading={loading}
            errorMessage={errorMessage}
            canRetry={Boolean(lastPayload)}
            onSendText={handleSendText}
            onSendAnswers={handleSendAnswers}
            onRetry={handleRetry}
          />
          <ResultPanel
            status={status}
            result={result}
            onDownloadDrawio={() =>
              sessionId &&
              void downloadDrawio(sessionId, result?.diagram_drawio_xml ?? null)
            }
          />
        </main>
      )}

      {showCostModal && (
        <CostModal telemetry={telemetry} onClose={() => setShowCostModal(false)} />
      )}
      {jsonModalData !== null && sessionId && (
        <JsonModal
          sessionId={sessionId}
          data={jsonModalData}
          onClose={() => setJsonModalData(null)}
        />
      )}
      {vendorItems !== null && (
        <VendorRequestsModal
          items={vendorItems}
          onClose={() => setVendorItems(null)}
        />
      )}
      {showModelsModal && (
        <ModelsMetaModal
          meta={modelsMeta}
          onClose={() => setShowModelsModal(false)}
        />
      )}
    </div>
  );
};

export default App;
