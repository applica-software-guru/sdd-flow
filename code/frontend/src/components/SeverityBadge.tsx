import type { BugSeverity } from '../types';

const severityColors: Record<BugSeverity, string> = {
  trivial: 'bg-slate-100 text-slate-700',
  minor: 'bg-yellow-100 text-yellow-700',
  major: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

export default function SeverityBadge({ severity }: { severity: BugSeverity }) {
  const color = severityColors[severity];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}
    >
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
}
