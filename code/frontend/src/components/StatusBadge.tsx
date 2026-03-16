import type { CRStatus, BugStatus, DocStatus } from '../types';

type Status = CRStatus | BugStatus | DocStatus;

const statusColors: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  applied: 'bg-indigo-100 text-indigo-700',
  in_progress: 'bg-indigo-100 text-indigo-700',
  open: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  wont_fix: 'bg-slate-100 text-slate-700',
  closed: 'bg-slate-100 text-slate-700',
  new: 'bg-blue-100 text-blue-700',
  changed: 'bg-yellow-100 text-yellow-700',
  synced: 'bg-green-100 text-green-700',
  deleted: 'bg-red-100 text-red-700',
};

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function StatusBadge({ status }: { status: Status }) {
  const color = statusColors[status] || 'bg-slate-100 text-slate-700';
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}
    >
      {formatStatus(status)}
    </span>
  );
}
