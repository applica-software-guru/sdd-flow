import { UserBrief } from '../types';

function initialsOf(name: string): string {
  return (
    name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase() || '?'
  );
}

/**
 * Table cell showing a resolved user with avatar initials;
 * renders an em-dash placeholder when there is no user (e.g. unassigned).
 */
export default function UserCell({ user, fallback = '--' }: { user?: UserBrief | null; fallback?: string }) {
  if (!user) {
    return <span className="text-slate-400 dark:text-slate-500">{fallback}</span>;
  }
  return (
    <div className="flex items-center gap-2">
      <div
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30 text-[10px] font-semibold text-blue-700 dark:text-blue-400"
        title={user.email}
      >
        {initialsOf(user.display_name)}
      </div>
      <span className="truncate text-sm text-slate-900 dark:text-slate-100" title={user.email}>
        {user.display_name}
      </span>
    </div>
  );
}
