import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAuditLog } from '../../hooks/useAuditLog';
import Pagination from '../../components/Pagination';
import EmptyState from '../../components/EmptyState';
import { DetailsCell } from '../../components/AuditDetailsCell';

function initialsOf(name: string): string {
  return (
    name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase() || '?'
  );
}

export default function AuditLogPage() {
  const { tenantId } = useParams();
  const [action, setAction] = useState('');
  const [entityType, setEntityType] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useAuditLog(tenantId, {
    action: action || undefined,
    entity_type: entityType || undefined,
    page,
    page_size: 25,
  });

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Audit Log</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Track all actions performed within this tenant
        </p>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setPage(1);
          }}
          placeholder="Filter by action..."
          className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm dark:text-slate-100 shadow-sm placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={entityType}
          onChange={(e) => {
            setEntityType(e.target.value);
            setPage(1);
          }}
          className="sdd-select rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm dark:text-slate-100 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All entity types</option>
          <option value="project">Project</option>
          <option value="change_request">Change Request</option>
          <option value="bug">Bug</option>
          <option value="document">Document</option>
          <option value="member">Member</option>
          <option value="api_key">API Key</option>
        </select>
        {data && (
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {data.total} entries
          </span>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No audit log entries"
            description="Actions performed in this tenant will appear here"
          />
        ) : (
          <>
            <table className="min-w-full table-fixed divide-y divide-slate-200 dark:divide-slate-700">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50">
                  <th className="w-44 px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Time
                  </th>
                  <th className="w-40 px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    User
                  </th>
                  <th className="w-28 px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Action
                  </th>
                  <th className="w-40 px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Entity
                  </th>
                  <th className="hidden w-[26rem] px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 lg:table-cell">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data.items.map((entry) => (
                  <tr key={entry.id} className="hover:bg-slate-50 dark:hover:bg-slate-700">
                    <td className="whitespace-nowrap px-6 py-3 text-sm text-slate-500 dark:text-slate-400">
                      {new Date(entry.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3">
                      {entry.user ? (
                        <div className="flex items-center gap-2">
                          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30 text-[10px] font-semibold text-blue-700 dark:text-blue-400">
                            {initialsOf(entry.user.display_name)}
                          </div>
                          <span className="truncate text-sm text-slate-900 dark:text-slate-100" title={entry.user.email}>
                            {entry.user.display_name}
                          </span>
                        </div>
                      ) : (
                        <span className="inline-flex rounded-full bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-xs font-medium italic text-slate-500 dark:text-slate-400">
                          System
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className="inline-flex max-w-full truncate rounded-full bg-slate-100 dark:bg-slate-700 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:text-slate-300"
                        title={entry.action}
                      >
                        {entry.action || entry.event_type}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm">
                      {entry.entity_label ? (
                        <span
                          className="block truncate font-medium text-slate-900 dark:text-slate-100"
                          title={entry.entity_label}
                        >
                          {entry.entity_label}
                        </span>
                      ) : entry.entity_id ? (
                        <span className="block truncate font-mono text-xs text-slate-500 dark:text-slate-400" title={entry.entity_id}>
                          {entry.entity_id.slice(0, 8)}...
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500">--</span>
                      )}
                      <span className="block text-xs capitalize text-slate-400 dark:text-slate-500">
                        {(entry.entity_type ?? '').replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="hidden max-w-0 px-6 py-3 text-xs text-slate-400 dark:text-slate-500 align-top lg:table-cell">
                      <DetailsCell entry={entry} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination
              page={data.page}
              totalPages={data.pages}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </div>
  );
}
