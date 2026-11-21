import React from 'react';
import {
  ModelsMetaResponse,
  TelemetryInfo,
  VendorRequestItem
} from '../types/api';
import { formatTokens, formatUsd } from '../utils/formatters';
import { triggerDownload } from '../api/client';

interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ title, onClose, children }) => (
  <div className="modal-backdrop" onClick={onClose}>
    <div className="modal-window" onClick={(e) => e.stopPropagation()}>
      <div className="modal-header">
        <h3>{title}</h3>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="modal-body">{children}</div>
    </div>
  </div>
);

export const CostModal: React.FC<{
  telemetry: TelemetryInfo;
  onClose: () => void;
}> = ({ telemetry, onClose }) => (
  <Modal title="Расходы текущей сессии" onClose={onClose}>
    <div className="cost-summary-grid">
      <div>
        <span>Итоговая стоимость (оценка):</span>
        <strong>
          {formatUsd(telemetry.total_cost_usd, telemetry.usage_status)}
        </strong>
      </div>
      {telemetry.provider_actual_cost_usd !== undefined &&
        telemetry.provider_actual_cost_usd !== null &&
        telemetry.provider_actual_cost_usd !== telemetry.total_cost_usd && (
          <div>
            <span>Фактическая стоимость провайдера (usage.cost):</span>
            <strong>{formatUsd(telemetry.provider_actual_cost_usd)}</strong>
          </div>
        )}
      <div>
        <span>Всего токенов (вход / выход):</span>
        <strong>
          {formatTokens(telemetry.total_input_tokens)} /{' '}
          {formatTokens(telemetry.total_output_tokens)}
        </strong>
      </div>
    </div>

    <div className="table-scroll">
      <table className="rules-table">
        <thead>
          <tr>
            <th>Модель</th>
            <th>Провайдер</th>
            <th>Вызовы</th>
            <th>Вход</th>
            <th>Выход</th>
            <th>Цена входа</th>
            <th>Цена выхода</th>
            <th>Итого</th>
          </tr>
        </thead>
        <tbody>
          {telemetry.models_breakdown.length === 0 ? (
            <tr>
              <td colSpan={8}>Вызовов моделей в этой сессии ещё не было.</td>
            </tr>
          ) : (
            telemetry.models_breakdown.map((m, idx) => (
              <tr key={idx}>
                <td>{m.model_id}</td>
                <td>{m.provider}</td>
                <td>{m.calls_count}</td>
                <td>{formatTokens(m.input_tokens)}</td>
                <td>{formatTokens(m.output_tokens)}</td>
                <td>{formatUsd(m.cost_input_usd, telemetry.usage_status)}</td>
                <td>{formatUsd(m.cost_output_usd, telemetry.usage_status)}</td>
                <td>
                  <strong>{formatUsd(m.cost_total_usd, telemetry.usage_status)}</strong>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </Modal>
);

export const JsonModal: React.FC<{
  sessionId: string;
  data: unknown;
  onClose: () => void;
}> = ({ sessionId, data, onClose }) => {
  const formatted = JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(formatted);
  };

  const handleDownload = () => {
    const blob = new Blob([formatted], { type: 'application/json;charset=utf-8' });
    triggerDownload(blob, `synonyx_result_${sessionId}.json`);
  };

  return (
    <Modal title="Служебный JSON для экспертной проверки" onClose={onClose}>
      <div className="modal-toolbar">
        <button type="button" className="btn btn-secondary btn-sm" onClick={handleCopy}>
          Копировать JSON
        </button>
        <button type="button" className="btn btn-primary btn-sm" onClick={handleDownload}>
          Скачать .json
        </button>
      </div>
      <pre className="json-pre">{formatted}</pre>
    </Modal>
  );
};

export const VendorRequestsModal: React.FC<{
  items: VendorRequestItem[];
  onClose: () => void;
}> = ({ items, onClose }) => (
  <Modal title="Пожелания для разработчика продукта" onClose={onClose}>
    {items.length === 0 ? (
      <p>В этой сессии неподдерживаемых пожеланий не зафиксировано.</p>
    ) : (
      <div className="table-scroll">
        <table className="rules-table">
          <thead>
            <tr>
              <th>Шаг</th>
              <th>Источник</th>
              <th>Исходный текст</th>
              <th>Потребность</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={idx}>
                <td>{it.turn_id}</td>
                <td>{it.source}</td>
                <td>{it.raw_text}</td>
                <td>{it.normalized_request}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </Modal>
);

export const ModelsMetaModal: React.FC<{
  meta: ModelsMetaResponse | null;
  onClose: () => void;
}> = ({ meta, onClose }) => (
  <Modal title="Модели рабочего контура и тарифы OpenRouter" onClose={onClose}>
    {!meta ? (
      <p>Загрузка...</p>
    ) : (
      <>
        <div className="table-scroll">
          <table className="rules-table">
            <thead>
              <tr>
                <th>Модель</th>
                <th>Провайдер</th>
                <th>Назначение</th>
                <th>Вход ($/1M)</th>
                <th>Выход ($/1M)</th>
              </tr>
            </thead>
            <tbody>
              {meta.models.map((m, idx) => (
                <tr key={idx}>
                  <td>
                    <a href={m.openrouter_url} target="_blank" rel="noreferrer">
                      {m.model_id}
                    </a>
                  </td>
                  <td>{m.provider}</td>
                  <td>{m.purpose}</td>
                  <td>${m.p_input_usd_per_1m}</td>
                  <td>${m.p_output_usd_per_1m}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {meta.knowledge_base_indexing_cost && (
          <div className="alert alert-info" style={{ marginTop: 12 }}>
            Однократная индексация базы знаний (не входит в стоимость сессий):{' '}
            <strong>
              {formatUsd(meta.knowledge_base_indexing_cost.total_cost_usd)}
            </strong>{' '}
            ({formatTokens(meta.knowledge_base_indexing_cost.total_tokens)} токенов).
          </div>
        )}
      </>
    )}
  </Modal>
);
