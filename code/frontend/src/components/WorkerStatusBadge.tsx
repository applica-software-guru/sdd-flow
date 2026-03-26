import type { WorkerStatus } from '../types';

const statusConfig: Record<WorkerStatus, { dot: string; text: string; bg: string }> = {
  online: {
    dot: 'bg-green-500',
    text: 'Online',
    bg: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400',
  },
  offline: {
    dot: 'bg-slate-400',
    text: 'Offline',
    bg: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300',
  },
  busy: {
    dot: 'bg-amber-500',
    text: 'Busy',
    bg: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400',
  },
};

export default function WorkerStatusBadge({ status }: { status: WorkerStatus }) {
  const config = statusConfig[status] || statusConfig.offline;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${config.bg}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {config.text}
    </span>
  );
}
