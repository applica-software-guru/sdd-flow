import { initialsOf } from '../utils/user';

interface UserNameProps {
  /** Display name to render (falls back to email, truncated, when missing). */
  name?: string | null;
  /** Email shown as `title` tooltip and only used as visible fallback text. */
  email?: string | null;
  /** Show the initials avatar before the name. */
  showAvatar?: boolean;
  /** Text when there is neither a name nor an email. */
  fallback?: string;
  className?: string;
}

/**
 * Shared user identity renderer (CR-035): the whole element can shrink inside
 * any flex/grid container (`min-w-0`), the name is always truncated and the
 * email is only a tooltip — long values can never overflow onto siblings.
 */
export default function UserName({
  name,
  email,
  showAvatar = true,
  fallback = '--',
  className = '',
}: UserNameProps) {
  if (!name && !email) {
    if (!showAvatar) {
      return <span className="text-slate-400 dark:text-slate-500">{fallback}</span>;
    }
    return (
      <span className={`flex min-w-0 items-center gap-2 ${className}`}>
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-[10px] font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
          ?
        </span>
        <span className="truncate text-sm text-slate-900 dark:text-slate-100">{fallback}</span>
      </span>
    );
  }
  const label = name || email || fallback;
  return (
    <span className={`flex min-w-0 items-center gap-2 ${className}`}>
      {showAvatar && (
        <span
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-[10px] font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
          title={email ?? undefined}
        >
          {initialsOf(name ?? email)}
        </span>
      )}
      <span
        className="truncate text-sm text-slate-900 dark:text-slate-100"
        title={email ?? undefined}
      >
        {label}
      </span>
    </span>
  );
}