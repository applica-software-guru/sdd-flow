import i18n, { normalizedLanguage, type SupportedLanguage } from '@/i18n';

/**
 * Formats an ISO date string as date-only (no time of day).
 */
function asValidDate(value: string | Date | undefined | null): Date | null {
  if (!value) return null;
  const date = typeof value === 'string' ? new Date(value) : value;
  return Number.isNaN(date.getTime()) ? null : date;
}

function activeLocale(locale?: SupportedLanguage): SupportedLanguage {
  return locale ?? normalizedLanguage(i18n.resolvedLanguage ?? i18n.language);
}

export function formatDateOnly(
  value: string | Date | undefined | null,
  locale?: SupportedLanguage
): string {
  const date = asValidDate(value);
  return date ? new Intl.DateTimeFormat(activeLocale(locale)).format(date) : '';
}

export function formatDateTime(
  value: string | Date | undefined | null,
  locale?: SupportedLanguage
): string {
  const date = asValidDate(value);
  return date
    ? new Intl.DateTimeFormat(activeLocale(locale), {
        dateStyle: 'short',
        timeStyle: 'short',
      }).format(date)
    : '';
}

export function formatNumber(value: number, locale?: SupportedLanguage): string {
  return new Intl.NumberFormat(activeLocale(locale)).format(value);
}
