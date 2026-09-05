export interface UserLabelParts {
  name?: string | null;
  display_name?: string | null;
  email?: string | null;
}

function nonEmpty(value?: string | null): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function preferredName(parts?: UserLabelParts | null): string | null {
  return nonEmpty(parts?.display_name) ?? nonEmpty(parts?.name);
}

/** Initials for avatar circles ("Jane Doe" -> "JD"), "?" when empty. */
export function initialsOf(name?: string | null): string {
  const normalized = nonEmpty(name);
  if (!normalized) return '?';
  return (
    normalized
      .split(/\s+/)
      .map((n) => n[0])
      .join('')
      .toUpperCase() || '?'
  );
}

/** Preferred visible user label: display name, then email, then fallback. */
export function userDisplayLabel(parts?: UserLabelParts | null, fallback = '--'): string {
  return preferredName(parts) ?? nonEmpty(parts?.email) ?? fallback;
}

/** Full text to expose in titles/tooltips for the visible user label. */
export function userLabelTitle(parts?: UserLabelParts | null): string | undefined {
  return preferredName(parts) ?? nonEmpty(parts?.email) ?? undefined;
}

/** Shorten labels for native/select option contexts where CSS truncation is unreliable. */
export function compactUserLabel(label?: string | null, max = 32, fallback = '--'): string {
  const normalized = nonEmpty(label) ?? fallback;
  if (max <= 0 || normalized.length <= max) return normalized;
  if (max === 1) return '…';
  return `${normalized.slice(0, max - 1)}…`;
}

/** Preferred compact label from user parts. */
export function compactUserDisplayLabel(
  parts?: UserLabelParts | null,
  max = 32,
  fallback = '--'
): string {
  return compactUserLabel(userDisplayLabel(parts, fallback), max, fallback);
}
