import UserName from './user-name';
import type { UserBrief } from '../types';

/**
 * Table cell showing a resolved user with avatar initials;
 * renders an em-dash placeholder when there is no user (e.g. unassigned).
 */
export default function UserCell({
  user,
  fallback = '--',
}: {
  user?: UserBrief | null;
  fallback?: string;
}) {
  if (!user) {
    return <span className="text-slate-400 dark:text-slate-500">{fallback}</span>;
  }
  return <UserName name={user.display_name} email={user.email} />;
}
