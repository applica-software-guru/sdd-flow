/**
 * Formats an ISO date string as date-only (no time of day).
 */
export function formatDateOnly(iso: string | Date | undefined | null): string {
  if (!iso) return '';
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString();
}
