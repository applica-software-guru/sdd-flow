import { useState } from 'react';
import { formatDateTime } from '@/lib/format';
import { initialsOf } from '../utils/user';
import type { Comment } from '../types';
import { translate } from '@/i18n';

/**
 * Compact comment author header: avatar initials + display name + timestamp.
 * The timestamp is aligned with the display name (both live in the same
 * column, to the right of the avatar). Reused by both CR and bug detail pages.
 */
export default function CommentHeader({ comment }: { comment: Comment }) {
  const name = comment.author?.display_name ?? null;
  const email = comment.author?.email ?? null;
  const avatarUrl = comment.author?.avatar_url ?? null;
  const [imageFailed, setImageFailed] = useState(false);
  const shouldShowImage = Boolean(avatarUrl) && !imageFailed;
  return (
    <div className="flex min-w-0 items-start gap-2 text-sm">
      {shouldShowImage ? (
        <img
          src={avatarUrl ?? undefined}
          alt=""
          className="h-7 w-7 shrink-0 rounded-full object-cover"
          title={email ?? undefined}
          onError={() => setImageFailed(true)}
        />
      ) : (
        <span
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
          title={email ?? undefined}
        >
          {initialsOf(name ?? email)}
        </span>
      )}
      <div className="min-w-0">
        <p className="truncate text-slate-900 dark:text-slate-100" title={email ?? undefined}>
          {name ?? translate('common:fallback.unknown')}
        </p>
        <p className="text-xs text-slate-400 dark:text-slate-500">
          {formatDateTime(comment.created_at)}
        </p>
      </div>
    </div>
  );
}
