import type { AuditLogEntry } from '../types';

/** Friendly labels for known detail keys; unknown keys are humanized as fallback. */
export const DETAIL_LABELS: Record<string, string> = {
  old_status: 'Previous status',
  new_status: 'New status',
  created: 'Created',
  updated: 'Updated',
  email: 'Email',
  role: 'Role',
  removed_user_id: 'Removed user ID',
  deleted_documents: 'Documents deleted',
  deleted_change_requests: 'Change requests deleted',
  deleted_bugs: 'Bugs deleted',
  deleted_comments: 'Comments deleted',
  deleted_notifications: 'Notifications deleted',
  deleted_workers: 'Workers deleted',
  deleted_jobs: 'Jobs deleted',
  deleted_messages: 'Messages deleted',
};

export function humanizeKey(key: string): string {
  const label = DETAIL_LABELS[key] ?? key.replace(/_/g, ' ');
  return label.charAt(0).toUpperCase() + label.slice(1);
}

/**
 * Human-readable fallback for legacy entries (created before summary was
 * captured): derive a description from the action without mutating the
 * append-only log. e.g. "bug.created" → "Created", "project.reset" → "Data reset".
 */
export const ACTION_LABELS: Record<string, string> = {
  created: 'Created',
  updated: 'Updated',
  deleted: 'Deleted',
  archived: 'Archived',
  restored: 'Restored',
  transitioned: 'Status changed',
  revoked: 'Revoked',
  reset: 'Data reset',
  bulk_upsert: 'Bulk upsert',
  joined: 'Joined',
  removed: 'Removed',
  cancelled: 'Cancelled',
};

export function describeAction(action: string): string {
  const suffix = action.split('.').slice(1).join('.');
  const label = ACTION_LABELS[suffix] ?? action.split('.').pop();
  if (!label) return action;
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function isPrimitive(value: unknown): boolean {
  return value === null || value === undefined || typeof value !== 'object';
}

export function DetailsCell({ entry }: { entry: AuditLogEntry }) {
  const detailsEntries = Object.entries(entry.details ?? {});
  const hasSummary = !!entry.summary;
  const allPrimitive = detailsEntries.every(([, v]) => isPrimitive(v));
  const showChips = detailsEntries.length > 0 && allPrimitive;
  const showJson = detailsEntries.length > 0 && !allPrimitive;

  if (!hasSummary && !showChips && !showJson) {
    // Legacy entry without summary/details: describe the action instead of an empty cell
    const action = entry.action || entry.event_type;
    if (action) return <span className="text-slate-500 dark:text-slate-400">{describeAction(action)}</span>;
    return <span className="text-slate-400 dark:text-slate-500">--</span>;
  }

  return (
    <div>
      {hasSummary && (
        <div className="text-xs font-medium text-slate-600 dark:text-slate-300">
          {entry.summary}
        </div>
      )}
      {showChips && (
        <div className={`flex flex-wrap gap-1 ${hasSummary ? 'mt-1.5' : ''}`}>
          {detailsEntries.map(([key, value]) => (
            <span
              key={key}
              className="inline-flex max-w-full items-baseline gap-1 rounded-md bg-slate-100 dark:bg-slate-900/40 px-1.5 py-0.5 text-[11px] leading-4"
            >
              <span className="text-slate-500 dark:text-slate-400">
                {humanizeKey(key)}:
              </span>
              <span className="font-mono text-slate-700 dark:text-slate-200 break-all">
                {value === null || value === undefined ? '—' : String(value)}
              </span>
            </span>
          ))}
        </div>
      )}
      {showJson && (
        <div
          className={`max-h-28 w-full overflow-auto rounded-md bg-slate-50 px-2 py-1 whitespace-pre-wrap break-all font-mono text-[11px] leading-5 text-slate-600 dark:bg-slate-900/40 dark:text-slate-300 ${
            hasSummary ? 'mt-1.5' : ''
          }`}
        >
          {JSON.stringify(entry.details, null, 2)}
        </div>
      )}
    </div>
  );
}
