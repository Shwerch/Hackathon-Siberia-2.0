import React, { useState } from 'react';
import { ProjectResult, SessionStatus } from '../types/api';
import { DrawioDiagramViewer } from './DrawioDiagramViewer';
import { MarkdownView } from './MarkdownView';

interface ResultPanelProps {
  status: SessionStatus;
  result: ProjectResult | null;
  onDownloadDrawio: () => void;
}

type ResultTab = 'diagram' | 'table' | 'explanation';

export const ResultPanel: React.FC<ResultPanelProps> = ({
  status,
  result,
  onDownloadDrawio
}) => {
  const [activeTab, setActiveTab] = useState<ResultTab>('diagram');

  if (!result) {
    return (
      <section className="result-panel result-empty">
        <div className="empty-state">
          <h3>Результат проектирования</h3>
          <p>
            После уточнения параметров здесь появятся интерактивная схема
            размещения «Синоникса», таблица минимального набора правил и кнопка
            скачивания редактируемого файла <code>.drawio</code>.
          </p>
        </div>
      </section>
    );
  }

  const renderFileUsersText = () => {
    if (result.file_users_count !== null && result.file_users_count !== undefined) {
      return String(result.file_users_count);
    }
    if (result.file_users_range) {
      const { min, max } = result.file_users_range;
      return max !== null ? `${min}–${max}` : `от ${min}`;
    }
    return 'неизвестно';
  };

  return (
    <section className="result-panel">
      <div className="result-summary-bar">
        <div className="summary-metrics">
          <div className="metric-box">
            <span className="metric-label">Правил Синоникса</span>
            <strong className="metric-value">
              {status === 'preliminary'
                ? `минимум ${result.rules_count}`
                : result.rules_count}
            </strong>
          </div>
          <div className="metric-box">
            <span className="metric-label">Файловых пользователей</span>
            <strong className="metric-value">{renderFileUsersText()}</strong>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={onDownloadDrawio}
          disabled={!result.has_diagram && !result.diagram_drawio_xml}
        >
          Скачать .drawio
        </button>
      </div>

      {status === 'preliminary' && (
        <div className="alert alert-warn">
          <strong>Предварительная оценка: минимум {result.rules_count} правил.</strong>
          {result.unknowns.length > 0 && (
            <div className="alert-list">
              Неизвестные параметры: {result.unknowns.join(', ')}.
            </div>
          )}
        </div>
      )}

      {result.assumptions.length > 0 && (
        <div className="alert alert-info">
          <strong>Принятые проектные допущения:</strong>{' '}
          {result.assumptions.join('; ')}
        </div>
      )}

      <div className="tabs-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'diagram' ? 'active' : ''}`}
          onClick={() => setActiveTab('diagram')}
        >
          Диаграмма
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'table' ? 'active' : ''}`}
          onClick={() => setActiveTab('table')}
        >
          Таблица правил ({result.rules.length})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'explanation' ? 'active' : ''}`}
          onClick={() => setActiveTab('explanation')}
        >
          Объяснение и ограничения
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'diagram' && (
          <div className="diagram-tab">
            {result.diagram_drawio_xml ? (
              <DrawioDiagramViewer xml={result.diagram_drawio_xml} />
            ) : (
              <div className="empty-state">
                <p>Схема будет построена после уточнения недостающих параметров.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'table' && (
          <div className="table-scroll">
            <table className="rules-table">
              <thead>
                <tr>
                  <th>№</th>
                  <th>Источник</th>
                  <th>Получатель</th>
                  <th>Тип</th>
                  <th>Режим</th>
                  <th>Протокол / Порт / Способ</th>
                  <th>Проверки</th>
                  <th>Обоснование</th>
                </tr>
              </thead>
              <tbody>
                {result.rules.map((rule) => {
                  const protoCell =
                    typeof rule.protocol === 'string' ? (
                      <span>
                        {rule.protocol}{' '}
                        {rule.port !== undefined && rule.port !== null ? (
                          <strong>{rule.port}</strong>
                        ) : (
                          <span className="unknown-badge">порт не указан</span>
                        )}
                      </span>
                    ) : (
                      <div className="file-proto">
                        <div>
                          <strong>Открытая:</strong> {rule.protocol.open}
                        </div>
                        <div>
                          <strong>Закрытая:</strong> {rule.protocol.closed}
                        </div>
                      </div>
                    );

                  return (
                    <tr key={rule.id}>
                      <td>{rule.id}</td>
                      <td>{rule.from}</td>
                      <td>{rule.to}</td>
                      <td>{rule.type === 'data' ? 'Данные' : 'Файлы'}</td>
                      <td>
                        {rule.mode === 'one-way'
                          ? 'Однонаправленное'
                          : 'Двунаправленное'}
                      </td>
                      <td>{protoCell}</td>
                      <td>
                        {rule.checks && rule.checks.length > 0
                          ? rule.checks.join(', ')
                          : '—'}
                      </td>
                      <td>{rule.rationale || rule.description}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'explanation' && (
          <div className="explanation-tab">
            <MarkdownView content={result.explanation} />

            {result.requests_for_vendor.length > 0 && (
              <div className="vendor-box">
                <h4>Эти пожелания можно передать разработчику продукта:</h4>
                <ul>
                  {result.requests_for_vendor.map((req, idx) => (
                    <li key={idx}>{req}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
