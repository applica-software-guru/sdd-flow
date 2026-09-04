import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useChangeRequests } from '../../hooks/useChangeRequests';
import PageContainer from '../../components/PageContainer';
import StatusBadge from '../../components/StatusBadge';
import Pagination from '../../components/Pagination';
import EmptyState from '../../components/EmptyState';
import UserCell from '../../components/UserCell';
import { formatDateOnly } from '../../lib/format';

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending', label: 'Pending' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'applied', label: 'Applied' },
  { value: 'closed', label: 'Closed' },
  { value: 'deleted', label: 'Deleted' },
];

export default function ListPage() {
  const { tenantId, projectId } = useParams();
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useChangeRequests(tenantId, projectId, {
    status: status || undefined,
    page,
    page_size: 20,
  });

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Change Requests
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Track and manage change requests for this project
          </p>
        </div>
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/crs/new`}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          New CR
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-4 flex items-center gap-3">
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          className="sdd-select rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {data && (
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {data.total} result{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No change requests"
            description={
              status
                ? 'No change requests match the selected filters'
                : 'Create your first change request to get started'
            }
          />
        ) : (
          <>
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Status
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 sm:table-cell dark:text-slate-400">
                    Author
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 md:table-cell dark:text-slate-400">
                    Assignee
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 lg:table-cell dark:text-slate-400">
                    Created
                  </th>
                  <th className="hidden px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500 lg:table-cell dark:text-slate-400">
                    Comments
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data.items.map((cr) => (
                  <tr key={cr.id} className="hover:bg-slate-50 dark:hover:bg-slate-700">
                    <td className="px-6 py-4">
                      <Link
                        to={`/tenants/${tenantId}/projects/${projectId}/crs/${cr.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        <span className="mr-1.5 font-mono text-slate-400 dark:text-slate-500">
                          #{cr.formatted_number}
                        </span>
                        {cr.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={cr.status} />
                    </td>
                    <td className="hidden px-6 py-4 sm:table-cell">
                      <UserCell user={cr.author} />
                    </td>
                    <td className="hidden px-6 py-4 md:table-cell">
                      <UserCell user={cr.assignee} fallback="Unassigned" />
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 lg:table-cell dark:text-slate-400">
                      {formatDateOnly(cr.created_at)}
                    </td>
                    <td className="hidden px-6 py-4 text-center text-sm text-slate-500 lg:table-cell dark:text-slate-400">
                      {typeof cr.comments_count === 'number' && cr.comments_count > 0 ? (
                        <span className="inline-flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
                          <svg className="h-4 w-4 text-slate-400 dark:text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                          </svg>
                          {cr.comments_count}
                        </span>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-600">&mdash;</span>
                      )}
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
    </PageContainer>
  );
}
