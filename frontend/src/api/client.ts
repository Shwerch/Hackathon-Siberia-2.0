import {
  ApiErrorBody,
  CreateSessionResponse,
  MessageResponse,
  ModelsMetaResponse,
  SendMessageRequest,
  SessionStateResponse,
  VendorRequestItem
} from '../types/api';

export class ApiError extends Error {
  public readonly retryable: boolean;
  public readonly code: string;

  constructor(message: string, retryable = true, code = 'API_ERROR') {
    super(message);
    this.retryable = retryable;
    this.code = code;
  }
}

type FlexibleErrorBody = Omit<ApiErrorBody, 'detail'> & {
  detail?:
    | string
    | {
        error?: {
          message?: string;
          retryable?: boolean;
          code?: string;
        };
      };
};

async function parseError(res: Response): Promise<ApiError> {
  try {
    const raw = (await res.json()) as FlexibleErrorBody;
    if (raw?.error?.message) {
      return new ApiError(
        raw.error.message,
        raw.error.retryable ?? true,
        raw.error.code ?? `HTTP_${res.status}`
      );
    }
    if (typeof raw?.detail === 'string') {
      return new ApiError(raw.detail, res.status >= 500, `HTTP_${res.status}`);
    }
    if (raw?.detail && typeof raw.detail === 'object') {
      if (raw.detail.error?.message) {
        return new ApiError(
          raw.detail.error.message,
          raw.detail.error.retryable ?? true,
          raw.detail.error.code ?? `HTTP_${res.status}`
        );
      }
      return new ApiError(JSON.stringify(raw.detail), res.status >= 500, `HTTP_${res.status}`);
    }
  } catch {
    // ignore JSON parse error
  }
  return new ApiError(
    `Ошибка сервера (${res.status}). Ваши введённые данные сохранены, попробуйте повторить запрос.`,
    true,
    `HTTP_${res.status}`
  );
}

export async function createSession(): Promise<CreateSessionResponse> {
  const res = await fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as CreateSessionResponse;
}

export async function getSession(sessionId: string): Promise<SessionStateResponse> {
  const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as SessionStateResponse;
}

export async function sendMessage(
  sessionId: string,
  payload: SendMessageRequest
): Promise<MessageResponse> {
  const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as MessageResponse;
}

export async function getExportJson(sessionId: string): Promise<unknown> {
  const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/export/json`);
  if (!res.ok) throw await parseError(res);
  return await res.json();
}

export async function downloadDrawio(
  sessionId: string,
  fallbackXml?: string | null
): Promise<void> {
  try {
    const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/export/drawio`);
    if (res.ok) {
      const blob = await res.blob();
      triggerDownload(blob, `synonyx_${sessionId}.drawio`);
      return;
    }
  } catch {
    // fallback to in-memory XML if provided
  }
  if (fallbackXml) {
    const blob = new Blob([fallbackXml], { type: 'application/xml;charset=utf-8' });
    triggerDownload(blob, `synonyx_${sessionId}.drawio`);
    return;
  }
  throw new ApiError('Не удалось скачать файл .drawio', true);
}

export async function downloadLogs(
  sessionId: string,
  format: 'jsonl' | 'csv' | 'json' = 'jsonl'
): Promise<void> {
  const res = await fetch(
    `/api/sessions/${encodeURIComponent(sessionId)}/export/logs?format=${format}`
  );
  if (!res.ok) throw await parseError(res);
  const blob = await res.blob();
  triggerDownload(blob, `synonyx_logs_${sessionId}.${format}`);
}

export async function getVendorRequests(
  sessionId: string
): Promise<VendorRequestItem[]> {
  const res = await fetch(
    `/api/sessions/${encodeURIComponent(sessionId)}/export/vendor-requests`
  );
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as VendorRequestItem[];
}

export async function getModelsMeta(): Promise<ModelsMetaResponse> {
  const res = await fetch('/api/meta/models');
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as ModelsMetaResponse;
}

export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
