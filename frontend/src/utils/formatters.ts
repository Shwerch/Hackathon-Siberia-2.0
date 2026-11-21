import { SessionStatus, UsageStatus } from '../types/api';

export function formatUsd(
  value: number | null | undefined,
  usageStatus?: UsageStatus
): string {
  if (usageStatus === 'unknown' || value === null || value === undefined) {
    return 'не подтверждено';
  }
  if (value === 0) {
    return '$0';
  }
  if (value > 0 && value < 0.000001) {
    return 'менее $0,000001';
  }
  const fixed = value.toFixed(6).replace(/0+$/, '').replace(/\.$/, '');
  return `$${fixed}`;
}

export function formatTokens(n: number | null | undefined): string {
  if (n === null || n === undefined) {
    return '—';
  }
  return n.toLocaleString('ru-RU');
}

export function getStatusLabel(status: SessionStatus): {
  text: string;
  tone: 'neutral' | 'warn' | 'ok' | 'danger';
} {
  switch (status) {
    case 'completed':
      return { text: 'Готово', tone: 'ok' };
    case 'preliminary':
      return { text: 'Предварительная оценка', tone: 'warn' };
    case 'unsupported':
      return { text: 'Ограничение продукта', tone: 'danger' };
    case 'needs_clarification':
    default:
      return { text: 'Требуются уточнения', tone: 'neutral' };
  }
}

export function generateUuid(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'req_' + Math.random().toString(36).slice(2) + '_' + Date.now().toString(36);
}
