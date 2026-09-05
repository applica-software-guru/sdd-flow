/**
 * Formats an ISO date string as date-only (no time of day).
 */
function asValidDate(value: string | Date | undefined | null): Date | null {
  if (!value) return null;
  const date = typeof value === 'string' ? new Date(value) : value;
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateOnly(value: string | Date | undefined | null): string {
  return asValidDate(value)?.toLocaleDateString() ?? '';
}

export function formatDateTime(value: string | Date | undefined | null): string {
  return asValidDate(value)?.toLocaleString() ?? '';
}
