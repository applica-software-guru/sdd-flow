import type { CRStatus, BugStatus, DocStatus } from '../types';

type Status = CRStatus | BugStatus | DocStatus;

const statusColors: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  rejected: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
  applied: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-400',
  in_progress: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-400',
  open: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  resolved: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  wont_fix: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  closed: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  changed: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400',
  synced: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  deleted: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
};

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function StatusBadge({ status }: { status: Status }) {
  const color = statusColors[status] || 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300';
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}
    >
      {formatStatus(status)}
    </span>
  );
}
