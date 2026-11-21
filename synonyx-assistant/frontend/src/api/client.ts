export interface NetworkItem {
  id: "open" | "closed";
  name: string;
  trust: "open" | "closed";
}

export interface RuleItem {
  id: number;
  type: "data" | "file";
  from: "open" | "closed";
  to: "open" | "closed";
  mode: "one-way" | "two-way";
  protocol: string | Record<string, string>;
  port: number | null;
  description: string;
  checks: string[];
  source_devices: string[];
  target_device?: string;
}

export interface ClarifyOption {
  id: string;
  label: string;
}

export interface ClarifyQuestion {
  question_id: string;
  flow_key?: string;
  field: string;
  text: string;
  options: ClarifyOption[];
  allow_unknown: boolean;
  allow_other: boolean;
}

export interface SourceRef {
  file: string;
  section: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  turn_id: number;
  questions: ClarifyQuestion[];
  sources: SourceRef[];
}

export interface CallLogEntry {
  call_id: string;
  model_id: string;
  purpose: string;
  status: string;
  usage_status: string;
  input_tokens: number | null;
  output_tokens: number | null;
  evaluation_cost_usd: number | null;
}

export interface SessionState {
  session_id: string;
  status: "needs_clarification" | "preliminary" | "completed" | "unsupported";
  networks: NetworkItem[];
  rules: RuleItem[];
  rules_count: number;
  file_users_count: number | null;
  file_users_range: { min: number; max: number | null } | null;
  unknowns: string[];
  requests_for_vendor: string[];
  sources: SourceRef[];
  messages: ChatMessage[];
  pending_questions: ClarifyQuestion[];
  last_explanation: string;
  drawio_xml: string;
  usage: {
    status: string;
    input_tokens: number;
    output_tokens: number;
    input_cost_usd: number;
    output_cost_usd: number;
    evaluation_cost_usd: number;
    actual_cost_usd: number | null;
    calls: CallLogEntry[];
  };
  timing: {
    turns: { turn_id: number; duration_seconds: number; status: string }[];
    mean_turn_seconds: number | null;
  };
}

export async function createSession(): Promise<SessionState> {
  const res = await fetch("/api/sessions", { method: "POST" });
  if (!res.ok) throw new Error("Не удалось создать сессию");
  return res.json();
}

export async function sendTurn(
  sessionId: string,
  message: string,
  clarificationAnswers: Record<string, { choice?: string; other_text?: string }> = {}
): Promise<SessionState> {
  const res = await fetch(`/api/sessions/${sessionId}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, clarification_answers: clarificationAnswers }),
  });
  if (!res.ok) throw new Error(`Ошибка сервера (${res.status})`);
  return res.json();
}

export async function fetchResultJson(sessionId: string): Promise<unknown> {
  const res = await fetch(`/api/sessions/${sessionId}/export/result.json`);
  if (!res.ok) throw new Error("Не удалось получить служебный JSON");
  return res.json();
}

export function formatUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "не подтверждено";
  if (value > 0 && value < 0.000001) return "менее $0,000001";
  return `$${value.toFixed(6).replace(".", ",")}`;
}
