import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAuditLog } from '../../hooks/useAuditLog';
import Pagination from '../../components/Pagination';
import EmptyState from '../../components/EmptyState';

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
          className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm dark:text-slate-100 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
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
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
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
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Entity
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 lg:table-cell">
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
                      <div className="flex items-center gap-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30 text-[10px] font-semibold text-blue-700 dark:text-blue-400">
                          {entry.user?.display_name
                            ?.split(' ')
                            .map((n) => n[0])
                            .join('')
                            .toUpperCase() || '?'}
                        </div>
                        <span className="text-sm text-slate-900 dark:text-slate-100">
                          {entry.user?.display_name || 'Unknown'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <span className="inline-flex rounded-full bg-slate-100 dark:bg-slate-700 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:text-slate-300">
                        {entry.action}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm text-slate-500 dark:text-slate-400">
                      <span className="capitalize">
                        {entry.entity_type.replace(/_/g, ' ')}
                      </span>
                      <span className="ml-1 text-xs text-slate-400 dark:text-slate-500">
                        {entry.entity_id.slice(0, 8)}...
                      </span>
                    </td>
                    <td className="hidden px-6 py-3 text-xs text-slate-400 dark:text-slate-500 lg:table-cell">
                      {entry.details
                        ? JSON.stringify(entry.details).slice(0, 80)
                        : '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </div>
  );
}
