export type SessionStatus =
  | 'needs_clarification'
  | 'preliminary'
  | 'completed'
  | 'unsupported';

export type UsageStatus = 'confirmed' | 'partial' | 'unknown';

export interface SourceRef {
  file: string;
  section: string;
}

export interface QuestionOption {
  id: string;
  label: string;
}

export interface ClarificationQuestion {
  question_id: string;
  text: string;
  multi_select: boolean;
  options: QuestionOption[];
  allow_unknown: boolean;
  unknown_label?: string;
  allow_other: boolean;
  other_label?: string;
}

export interface QuestionAnswerPayload {
  question_id: string;
  selected_options: string[];
  is_unknown: boolean;
  other_text: string | null;
}

export interface NetworkNode {
  id: 'open' | 'closed' | string;
  name: string;
  trust: 'open' | 'closed';
}

export interface FileProtocolSide {
  open: string;
  closed: string;
}

export interface RuleItem {
  id: number;
  type: 'data' | 'file';
  from: string;
  to: string;
  mode: 'one-way' | 'two-way';
  protocol: string | FileProtocolSide;
  port?: number | null;
  checks?: string[];
  checks_by_node?: {
    node_a?: string[];
    node_b?: string[];
  };
  description: string;
  rationale?: string;
}

export interface FileUsersRange {
  min: number;
  max: number | null;
}

export interface ProjectResult {
  has_diagram: boolean;
  status_label?: string;
  explanation: string;
  networks: NetworkNode[];
  firewall: { side: 'open' | 'both' | string };
  synonyx: {
    location: 'closed' | string;
    node_a_faces: string;
    node_b_faces: string;
  };
  rules: RuleItem[];
  rules_count: number;
  file_users_count: number | null;
  file_users_range?: FileUsersRange | null;
  unknowns: string[];
  assumptions: string[];
  requests_for_vendor: string[];
  diagram_drawio_xml?: string | null;
}

export interface ModelBreakdownItem {
  model_id: string;
  provider: string;
  calls_count: number;
  input_tokens: number;
  output_tokens: number;
  cost_input_usd: number | null;
  cost_output_usd: number | null;
  cost_total_usd: number | null;
}

export interface TelemetryInfo {
  turn_timing_ms?: number;
  usage_status: UsageStatus;
  total_cost_usd: number | null;
  provider_actual_cost_usd?: number | null;
  total_input_tokens: number;
  total_output_tokens: number;
  models_breakdown: ModelBreakdownItem[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  sources?: SourceRef[];
  clarification_questions?: ClarificationQuestion[];
  timestamp: string;
}

export interface CreateSessionResponse {
  session_id: string;
  status: SessionStatus;
  welcome_message: string;
  example_prompt: string;
  telemetry: TelemetryInfo;
}

export interface SendMessageRequest {
  client_request_id: string;
  text: string;
  answers: QuestionAnswerPayload[];
}

export interface MessageResponse {
  session_id: string;
  turn_id: number;
  status: SessionStatus;
  assistant_message: {
    text: string;
    sources?: SourceRef[];
    clarification_questions?: ClarificationQuestion[];
  };
  result: ProjectResult | null;
  telemetry: TelemetryInfo;
}

export interface SessionStateResponse {
  session_id: string;
  status: SessionStatus;
  welcome_message?: string;
  example_prompt?: string;
  messages: ChatMessage[];
  result: ProjectResult | null;
  telemetry: TelemetryInfo;
}

export interface VendorRequestItem {
  session_id: string;
  turn_id: number;
  source: 'unsupported_request' | 'other_option' | string;
  raw_text: string;
  normalized_request: string;
  created_at: string;
}

export interface ModelsMetaResponse {
  models: Array<{
    model_id: string;
    provider: string;
    purpose: string;
    openrouter_url: string;
    p_input_usd_per_1m: number;
    p_output_usd_per_1m: number;
  }>;
  knowledge_base_indexing_cost?: {
    total_cost_usd: number | null;
    total_tokens: number;
    note?: string;
  };
}

export interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    retryable?: boolean;
    client_request_id?: string;
  };
  detail?: string;
}
