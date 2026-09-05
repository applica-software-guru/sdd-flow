import { initialsOf } from '../utils/user';
import type { Comment } from '../types';

/**
 * Compact comment author header: avatar initials + display name + timestamp.
 * The timestamp is aligned with the display name (both live in the same
 * column, to the right of the avatar). Reused by both CR and bug detail pages.
 */
export default function CommentHeader({ comment }: { comment: Comment }) {
  const name = comment.author?.display_name ?? null;
  const email = comment.author?.email ?? null;
  return (
    <div className="flex min-w-0 items-start gap-2 text-sm">
      <span
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
        title={email ?? undefined}
      >
        {initialsOf(name ?? email)}
      </span>
      <div className="min-w-0">
        <p className="truncate text-slate-900 dark:text-slate-100" title={email ?? undefined}>
          {name ?? 'Unknown'}
        </p>
        <p className="text-xs text-slate-400 dark:text-slate-500">
          {new Date(comment.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
