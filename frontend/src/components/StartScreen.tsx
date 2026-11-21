import React, { useState } from 'react';

interface StartScreenProps {
  welcomeMessage: string;
  examplePrompt: string;
  loading: boolean;
  errorMessage: string | null;
  onSend: (text: string) => void;
  onRetry: () => void;
}

export const StartScreen: React.FC<StartScreenProps> = ({
  welcomeMessage,
  examplePrompt,
  loading,
  errorMessage,
  onSend,
  onRetry
}) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const trimmed = text.trim();
      if (trimmed && !loading) {
        onSend(trimmed);
      }
    }
  };

  return (
    <main className="start-screen">
      <div className="start-card">
        <h1>Ассистент проектирования СКИО «Синоникс» (v1.9)</h1>
        <p className="start-lead">{welcomeMessage}</p>

        <div className="example-box">
          <div className="example-header">
            <span>Пример описания двух сетей и потоков</span>
            <div className="example-actions">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setText(examplePrompt)}
                disabled={loading}
              >
                Подставить в поле
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => onSend(examplePrompt)}
                disabled={loading}
              >
                Запустить пример
              </button>
            </div>
          </div>
          <blockquote className="example-quote">{examplePrompt}</blockquote>
        </div>

        {errorMessage && (
          <div className="error-banner">
            <span>{errorMessage}</span>
            <button type="button" className="btn btn-danger btn-sm" onClick={onRetry}>
              Повторить запрос
            </button>
          </div>
        )}

        <form className="start-form" onSubmit={handleSubmit}>
          <textarea
            className="chat-textarea"
            rows={4}
            placeholder="Опишите две сети, какие системы обмениваются данными или файлами, протоколы, порты и нужные проверки..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <div className="start-form-footer">
            <span className="hint-text">
              Enter — отправить, Shift + Enter — перенос строки. Если параметров не
              хватает, ассистент задаст уточняющие вопросы.
            </span>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !text.trim()}
            >
              {loading ? 'Анализирую запрос...' : 'Отправить'}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
};
