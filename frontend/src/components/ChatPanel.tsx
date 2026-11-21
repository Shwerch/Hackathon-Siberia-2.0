import React, { useEffect, useRef, useState } from 'react';
import {
  ChatMessage,
  ClarificationQuestion,
  QuestionAnswerPayload
} from '../types/api';

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  errorMessage: string | null;
  canRetry: boolean;
  onSendText: (text: string) => void;
  onSendAnswers: (answers: QuestionAnswerPayload[], extraText: string) => void;
  onRetry: () => void;
}

interface QuestionDraftState {
  selected: string[];
  isUnknown: boolean;
  isOther: boolean;
  otherText: string;
}

const QuestionsCard: React.FC<{
  questions: ClarificationQuestion[];
  disabled: boolean;
  onSubmit: (answers: QuestionAnswerPayload[]) => void;
}> = ({ questions, disabled, onSubmit }) => {
  const [drafts, setDrafts] = useState<Record<string, QuestionDraftState>>(() => {
    const init: Record<string, QuestionDraftState> = {};
    questions.forEach((q) => {
      init[q.question_id] = {
        selected: [],
        isUnknown: false,
        isOther: false,
        otherText: ''
      };
    });
    return init;
  });

  const toggleOption = (q: ClarificationQuestion, optId: string) => {
    setDrafts((prev) => {
      const cur = prev[q.question_id] ?? {
        selected: [],
        isUnknown: false,
        isOther: false,
        otherText: ''
      };
      let nextSelected: string[];
      if (q.multi_select) {
        nextSelected = cur.selected.includes(optId)
          ? cur.selected.filter((x) => x !== optId)
          : [...cur.selected, optId];
      } else {
        nextSelected = [optId];
      }
      return {
        ...prev,
        [q.question_id]: {
          ...cur,
          selected: nextSelected,
          isUnknown: false
        }
      };
    });
  };

  const selectUnknown = (qId: string) => {
    setDrafts((prev) => ({
      ...prev,
      [qId]: {
        selected: [],
        isUnknown: true,
        isOther: false,
        otherText: ''
      }
    }));
  };

  const toggleOther = (q: ClarificationQuestion) => {
    setDrafts((prev) => {
      const cur = prev[q.question_id];
      const nextOther = !cur.isOther;
      return {
        ...prev,
        [q.question_id]: {
          ...cur,
          selected: q.multi_select ? cur.selected : [],
          isUnknown: false,
          isOther: nextOther,
          otherText: nextOther ? cur.otherText : ''
        }
      };
    });
  };

  const setOtherText = (qId: string, val: string) => {
    setDrafts((prev) => ({
      ...prev,
      [qId]: {
        ...prev[qId],
        isUnknown: false,
        isOther: true,
        otherText: val
      }
    }));
  };

  const isAllAnswered = questions.every((q) => {
    const d = drafts[q.question_id];
    if (!d) return false;
    if (d.isUnknown) return true;
    if (d.selected.length > 0) return true;
    if (d.isOther && d.otherText.trim().length > 0) return true;
    return false;
  });

  const handleApply = () => {
    const payload: QuestionAnswerPayload[] = questions.map((q) => {
      const d = drafts[q.question_id];
      return {
        question_id: q.question_id,
        selected_options: d.selected,
        is_unknown: d.isUnknown,
        other_text: d.isOther && d.otherText.trim() ? d.otherText.trim() : null
      };
    });
    onSubmit(payload);
  };

  return (
    <div className="questions-card">
      {questions.map((q) => {
        const d = drafts[q.question_id];
        return (
          <div key={q.question_id} className="question-item">
            <div className="question-title">{q.text}</div>
            <div className="question-options">
              {q.options.map((opt) => {
                const active = d.selected.includes(opt.id);
                return (
                  <button
                    key={opt.id}
                    type="button"
                    disabled={disabled}
                    className={`option-chip ${active ? 'active' : ''}`}
                    onClick={() => toggleOption(q, opt.id)}
                  >
                    {opt.label}
                  </button>
                );
              })}
              {q.allow_unknown && (
                <button
                  type="button"
                  disabled={disabled}
                  className={`option-chip option-unknown ${d.isUnknown ? 'active' : ''}`}
                  onClick={() => selectUnknown(q.question_id)}
                >
                  {q.unknown_label || 'Не знаю'}
                </button>
              )}
              {q.allow_other && (
                <button
                  type="button"
                  disabled={disabled}
                  className={`option-chip option-other ${d.isOther ? 'active' : ''}`}
                  onClick={() => toggleOther(q)}
                >
                  {q.other_label || 'Другое'}
                </button>
              )}
            </div>
            {q.allow_other && d.isOther && (
              <input
                type="text"
                className="other-input"
                placeholder="Укажите свой вариант..."
                disabled={disabled}
                value={d.otherText}
                onChange={(e) => setOtherText(q.question_id, e.target.value)}
              />
            )}
          </div>
        );
      })}
      <div className="questions-footer">
        <button
          type="button"
          className="btn btn-primary btn-sm"
          disabled={disabled || !isAllAnswered}
          onClick={handleApply}
        >
          Отправить ответы
        </button>
      </div>
    </div>
  );
};

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  loading,
  errorMessage,
  canRetry,
  onSendText,
  onSendAnswers,
  onRetry
}) => {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    setInput('');
    onSendText(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const trimmed = input.trim();
      if (trimmed && !loading) {
        setInput('');
        onSendText(trimmed);
      }
    }
  };

  const lastAssistantIdx = messages.reduce(
    (acc, m, idx) => (m.role === 'assistant' ? idx : acc),
    -1
  );

  return (
    <section className="chat-panel">
      <div className="chat-messages">
        {messages.map((msg, idx) => {
          const isLastAssistant = idx === lastAssistantIdx;
          return (
            <div key={msg.id} className={`chat-bubble chat-${msg.role}`}>
              <div className="chat-role">
                {msg.role === 'user' ? 'Вы' : 'Ассистент «Синоникс»'}
              </div>
              <div className="chat-text">{msg.text}</div>

              {msg.sources && msg.sources.length > 0 && (
                <div className="chat-sources">
                  <span className="sources-title">Источники:</span>
                  {msg.sources.map((src, sIdx) => (
                    <span key={sIdx} className="source-tag">
                      {src.file} ({src.section})
                    </span>
                  ))}
                </div>
              )}

              {msg.clarification_questions &&
                msg.clarification_questions.length > 0 && (
                  <QuestionsCard
                    questions={msg.clarification_questions}
                    disabled={loading || !isLastAssistant}
                    onSubmit={(answers) => onSendAnswers(answers, '')}
                  />
                )}
            </div>
          );
        })}

        {loading && (
          <div className="chat-bubble chat-assistant loading-bubble">
            <div className="spinner" />
            <span>Обрабатываю запрос, пересчитываю правила и схему...</span>
          </div>
        )}

        {errorMessage && (
          <div className="error-banner">
            <span>{errorMessage}</span>
            {canRetry && (
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={onRetry}
                disabled={loading}
              >
                Повторить запрос
              </button>
            )}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          className="chat-textarea"
          rows={2}
          placeholder="Задайте вопрос по схеме, уточните параметры или попросите внести изменения..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !input.trim()}
        >
          Отправить
        </button>
      </form>
    </section>
  );
};
