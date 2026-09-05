import UserName from '@/components/user-name';
import { formatDateTime } from '@/lib/format';
import { useState } from 'react';
import { AssignmentHistoryEntry, UserBrief } from '../types';
import { translate } from '@/i18n';

interface AssignmentPanelProps {
  author?: UserBrief | null;
  assigneeId: string | null | undefined;
  assignee?: UserBrief | null;
  members: { user_id: string; display_name: string }[];
  history?: AssignmentHistoryEntry[];
  onAssign: (assigneeId: string | null) => void;
  assigning: boolean;
}

/**
 * Inline author / assignee / assign-to control band shown inside the CR/bug
 * detail page transition section (not a standalone card).
 */
export default function AssignmentPanel({
  author,
  assigneeId,
  assignee,
  members,
  history,
  onAssign,
  assigning,
}: AssignmentPanelProps) {
  // Normalize to a string so the comparison below can't mismatch types
  // ('' !== null would be true forever → infinite render loop on unassigned items).
  const normalizedAssigneeId = assigneeId ?? '';
  const [selected, setSelected] = useState(normalizedAssigneeId);
  // Reset the local selection when the assignee changes externally
  // (render-time reset, see "You Might Not Need an Effect").
  const [prevAssigneeId, setPrevAssigneeId] = useState(normalizedAssigneeId);
  if (prevAssigneeId !== normalizedAssigneeId) {
    setPrevAssigneeId(normalizedAssigneeId);
    setSelected(normalizedAssigneeId);
  }

  const currentAssignee =
    assignee ?? history?.find((h) => h.assignee_id === assigneeId)?.assignee ?? null;
  const currentAssigneeName =
    currentAssignee?.display_name ?? members.find((m) => m.user_id === assigneeId)?.display_name;

  const handleChange = (value: string) => {
    setSelected(value);
    onAssign(value === '' ? null : value);
  };

  return (
    <div className="grid gap-6 sm:grid-cols-3">
      <div>
        <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {translate('common:auto.author')}
        </h3>
        <div className="mt-1">
          <UserName
            name={author?.display_name}
            email={author?.email}
            avatarUrl={author?.avatar_url}
            fallback="--"
          />
        </div>
      </div>
      <div>
        <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {translate('common:auto.assignee')}
        </h3>
        <div className="mt-1">
          {currentAssignee ? (
            <UserName
              name={currentAssignee.display_name}
              email={currentAssignee.email}
              avatarUrl={currentAssignee.avatar_url}
            />
          ) : (
            <span className="min-w-0 truncate text-sm text-slate-900 dark:text-slate-100">
              {currentAssigneeName ?? translate('common:fallback.unassigned')}
            </span>
          )}
        </div>
      </div>
      <div>
        <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {translate('common:auto.assign_to')}
        </h3>
        <select
          value={selected}
          onChange={(e) => handleChange(e.target.value)}
          disabled={assigning}
          className="sdd-select mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        >
          <option value="">{translate('common:auto.unassigned')}</option>
          {members.map((m) => (
            <option key={m.user_id} value={m.user_id}>
              {m.display_name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export function AssignmentHistory({
  history,
  entityLabel,
}: {
  history?: AssignmentHistoryEntry[];
  entityLabel: string;
}) {
  if (!history || history.length === 0) return null;
  return (
    <details className="mt-4">
      <summary className="cursor-pointer text-xs font-medium uppercase tracking-wider text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300">
        {translate('common:auto.assignment_history')}
        {history.length})
      </summary>
      <ul className="mt-3 space-y-2">
        {history.map((h) => (
          <li
            key={h.id}
            className="flex min-w-0 items-center gap-2 text-sm text-slate-600 dark:text-slate-300"
          >
            <span className="shrink-0 text-slate-400 dark:text-slate-500">
              {formatDateTime(h.created_at)}
            </span>
            <span className="min-w-0 truncate">
              {h.assignee ? (
                <UserName
                  name={h.assignee.display_name}
                  email={h.assignee.email}
                  avatarUrl={h.assignee.avatar_url}
                />
              ) : (
                translate('common:auto.unassigned_2')
              )}
            </span>
            {h.assigned_by_name && (
              <span className="min-w-0 truncate text-slate-400 dark:text-slate-500">
                {translate('common:auto.by')} {h.assigned_by_name}
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="sr-only">
        {translate('common:auto.assignment_history_for')} {entityLabel}
      </p>
    </details>
  );
}
