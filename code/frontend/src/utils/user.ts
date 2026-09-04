/** Initials for avatar circles ("Jane Doe" -> "JD"), "?" when empty. */
export function initialsOf(name?: string | null): string {
  if (!name) return '?';
  return (
    name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase() || '?'
  );
}