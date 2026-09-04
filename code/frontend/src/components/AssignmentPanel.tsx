import { useState } from 'react';
import { AssignmentHistoryEntry, UserBrief } from '../types';

interface AssignmentPanelProps {
  author?: UserBrief | null;
  assigneeId: string | null | undefined;
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

  const currentAssigneeName =
    members.find((m) => m.user_id === assigneeId)?.display_name ??
    history?.find((h) => h.assignee_id === assigneeId)?.assignee?.display_name;

  const handleChange = (value: string) => {
    setSelected(value);
    onAssign(value === '' ? null : value);
  };

  return (
    <div className="grid gap-6 sm:grid-cols-3">
      <div>
        <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Author
        </h3>
        <p className="mt-1 min-w-0 truncate text-sm text-slate-900 dark:text-slate-100" title={author?.email}>
          {author?.display_name ?? '--'}
        </p>
      </div>
      <div>
        <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Assignee
        </h3>
        <p className="mt-1 min-w-0 truncate text-sm text-slate-900 dark:text-slate-100">
          {currentAssigneeName ?? 'Unassigned'}
        </p>
      </div>
      <div>
        <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Assign to
        </h3>
        <select
          value={selected}
          onChange={(e) => handleChange(e.target.value)}
          disabled={assigning}
          className="sdd-select mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
        >
          <option value="">Unassigned</option>
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
        Assignment history ({history.length})
      </summary>
      <ul className="mt-3 space-y-2">
        {history.map((h) => (
          <li key={h.id} className="flex min-w-0 items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <span className="shrink-0 text-slate-400 dark:text-slate-500">
              {new Date(h.created_at).toLocaleString()}
            </span>
            <span className="min-w-0 truncate">
              {h.assignee
                ? `assigned to ${h.assignee.display_name}`
                : 'unassigned'}
            </span>
            {h.assigned_by_name && (
              <span className="min-w-0 truncate text-slate-400 dark:text-slate-500">
                by {h.assigned_by_name}
              </span>
            )}
          </li>
        ))}
      </ul>
      <p className="sr-only">Assignment history for {entityLabel}</p>
    </details>
  );
}
