import type { Comment } from '../types';

function initialsOf(name?: string): string {
  if (!name) return '?';
  return (
    name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase() || '?'
  );
}

/**
 * Compact comment author header: avatar initials + display name + timestamp.
 * Reused by both CR and bug detail pages.
 */
export default function CommentHeader({ comment }: { comment: Comment }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
        title={comment.author?.email}
      >
        {initialsOf(comment.author?.display_name)}
      </div>
      <div className="min-w-0">
        <p className="truncate text-slate-900 dark:text-slate-100">
          {comment.author?.display_name ?? 'Unknown'}
        </p>
        <p className="text-xs text-slate-400 dark:text-slate-500">
          {new Date(comment.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
