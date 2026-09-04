import { useState, useEffect } from 'react';
import { AssignmentHistoryEntry, UserBrief } from '../types';

interface AssignmentPanelProps {
  author?: UserBrief | null;
  assigneeId: string | null | undefined;
  members: { user_id: string; display_name: string }[];
  history?: AssignmentHistoryEntry[];
  onAssign: (assigneeId: string | null) => void;
  assigning: boolean;
  entityLabel: string;
}

/**
 * Metadata + control section shown on CR/bug detail pages: who authored the
 * item, who is currently assigned, a select to reassign/unassign and the
 * append-only assignment history.
 */
export default function AssignmentPanel({
  author,
  assigneeId,
  members,
  history,
  onAssign,
  assigning,
  entityLabel,
}: AssignmentPanelProps) {
  const [selected, setSelected] = useState(assigneeId ?? '');

  useEffect(() => {
    setSelected(assigneeId ?? '');
  }, [assigneeId]);

  const currentAssigneeName =
    members.find((m) => m.user_id === assigneeId)?.display_name ??
    history?.find((h) => h.assignee_id === assigneeId)?.assignee?.display_name;

  const handleChange = (value: string) => {
    setSelected(value);
    onAssign(value === '' ? null : value);
  };

  return (
    <div className="mb-6 rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="grid gap-6 border-b border-slate-200 px-6 py-4 sm:grid-cols-3 dark:border-slate-700">
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Author
          </h3>
          <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">
            {author?.display_name ?? '--'}
          </p>
        </div>
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Assignee
          </h3>
          <p className="mt-1 text-sm text-slate-900 dark:text-slate-100">
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

      {history && history.length > 0 && (
        <details className="px-6 py-3">
          <summary className="cursor-pointer text-xs font-medium uppercase tracking-wider text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300">
            Assignment history ({history.length})
          </summary>
          <ul className="mt-3 space-y-2">
            {history.map((h) => (
              <li key={h.id} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <span className="text-slate-400 dark:text-slate-500">
                  {new Date(h.created_at).toLocaleString()}
                </span>
                <span>
                  {h.assignee
                    ? `assigned to ${h.assignee.display_name}`
                    : 'unassigned'}
                </span>
                {h.assigned_by_name && (
                  <span className="text-slate-400 dark:text-slate-500">
                    by {h.assigned_by_name}
                  </span>
                )}
              </li>
            ))}
          </ul>
          <p className="sr-only">Assignment history for {entityLabel}</p>
        </details>
      )}
    </div>
  );
}
