import React from 'react';
import { SessionStatus, TelemetryInfo } from '../types/api';
import { formatTokens, formatUsd, getStatusLabel } from '../utils/formatters';

interface HeaderProps {
  sessionId: string | null;
  status: SessionStatus;
  telemetry: TelemetryInfo;
  hasResult: boolean;
  onNewSession: () => void;
  onOpenCostModal: () => void;
  onOpenJsonModal: () => void;
  onDownloadLogs: (format: 'jsonl' | 'csv') => void;
  onOpenVendorModal: () => void;
  onOpenModelsModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  sessionId,
  status,
  telemetry,
  hasResult,
  onNewSession,
  onOpenCostModal,
  onOpenJsonModal,
  onDownloadLogs,
  onOpenVendorModal,
  onOpenModelsModal
}) => {
  const badge = getStatusLabel(status);

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="brand">
          <span className="brand-accent">СИНОНИКС 1.9</span>
          <span className="brand-sub">Проектировщик схемы обмена</span>
        </div>
        {sessionId && (
          <div className="session-meta">
            <span className="session-id" title={sessionId}>
              Сессия: {sessionId.slice(0, 12)}
            </span>
            <span className={`status-pill status-${badge.tone}`}>{badge.text}</span>
          </div>
        )}
        <button type="button" className="btn btn-primary btn-sm" onClick={onNewSession}>
          + Новая сессия
        </button>
      </div>

      <div className="header-right">
        <button
          type="button"
          className="telemetry-widget"
          onClick={onOpenCostModal}
          title="Нажмите для подробной разбивки по моделям"
        >
          <span className="telemetry-item">
            <span className="telemetry-label">Расход:</span>
            <strong className="telemetry-value">
              {formatUsd(telemetry.total_cost_usd, telemetry.usage_status)}
            </strong>
          </span>
          <span className="telemetry-sep">|</span>
          <span className="telemetry-item">
            <span className="telemetry-label">Токены (вх/вых):</span>
            <strong>
              {formatTokens(telemetry.total_input_tokens)} /{' '}
              {formatTokens(telemetry.total_output_tokens)}
            </strong>
          </span>
          {telemetry.turn_timing_ms !== undefined && (
            <>
              <span className="telemetry-sep">|</span>
              <span className="telemetry-item">
                <span className="telemetry-label">Шаг:</span>
                <strong>{(telemetry.turn_timing_ms / 1000).toFixed(2)} с</strong>
              </span>
            </>
          )}
        </button>

        <div className="expert-actions">
          {sessionId && (
            <>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={onOpenJsonModal}
                disabled={!hasResult}
                title="Служебный JSON для экспертной проверки"
              >
                JSON
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onDownloadLogs('jsonl')}
                title="Скачать журнал вызовов, расходов и тайминга (JSONL)"
              >
                Лог JSONL
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => onDownloadLogs('csv')}
                title="Скачать журнал вызовов (CSV)"
              >
                Лог CSV
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={onOpenVendorModal}
                title="Зафиксированные пожелания для разработчика продукта"
              >
                Пожелания
              </button>
            </>
          )}
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onOpenModelsModal}
            title="Список моделей и тарифов OpenRouter"
          >
            Модели
          </button>
        </div>
      </div>
    </header>
  );
};
