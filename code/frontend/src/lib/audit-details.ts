import { translate } from '@/i18n';

const DETAIL_KEYS = new Set([
  'old_status',
  'new_status',
  'created',
  'updated',
  'email',
  'role',
  'removed_user_id',
  'deleted_documents',
  'deleted_change_requests',
  'deleted_bugs',
  'deleted_comments',
  'deleted_notifications',
  'deleted_workers',
  'deleted_jobs',
  'deleted_messages',
]);

export function humanizeKey(key: string): string {
  const fallback = key.replace(/_/g, ' ').replace(/^\w/, (letter) => letter.toUpperCase());
  return DETAIL_KEYS.has(key)
    ? translate(`audit:detail.${key}`, { defaultValue: fallback })
    : fallback;
}

const ACTION_KEYS = new Set([
  'created',
  'updated',
  'deleted',
  'archived',
  'restored',
  'transitioned',
  'revoked',
  'reset',
  'bulk_upsert',
  'joined',
  'removed',
  'cancelled',
]);

/** Returns a localized fallback summary for legacy audit entries. */
export function describeAction(action: string): string {
  const suffix = action.split('.').slice(1).join('.');
  const fallback = (action.split('.').pop() ?? action)
    .replace(/_/g, ' ')
    .replace(/^\w/, (letter) => letter.toUpperCase());
  return ACTION_KEYS.has(suffix)
    ? translate(`audit:action.${suffix}`, { defaultValue: fallback })
    : fallback;
}
