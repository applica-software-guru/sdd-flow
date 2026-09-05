/** Friendly labels for known audit detail keys; unknown keys are humanized as fallback. */
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
 * Human-readable fallback for legacy audit entries (created before summary was
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
