import { AuditLogEntry } from '../types';
import { describeAction, humanizeKey } from '../lib/audit-details';

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
    if (action)
      return <span className="text-slate-500 dark:text-slate-400">{describeAction(action)}</span>;
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
              className="inline-flex max-w-full items-baseline gap-1 rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] leading-4 dark:bg-slate-900/40"
            >
              <span className="text-slate-500 dark:text-slate-400">{humanizeKey(key)}:</span>
              <span className="break-all font-mono text-slate-700 dark:text-slate-200">
                {value === null || value === undefined ? '—' : String(value)}
              </span>
            </span>
          ))}
        </div>
      )}
      {showJson && (
        <div
          className={`max-h-28 w-full overflow-auto whitespace-pre-wrap break-all rounded-md bg-slate-50 px-2 py-1 font-mono text-[11px] leading-5 text-slate-600 dark:bg-slate-900/40 dark:text-slate-300 ${
            hasSummary ? 'mt-1.5' : ''
          }`}
        >
          {JSON.stringify(entry.details, null, 2)}
        </div>
      )}
    </div>
  );
}
