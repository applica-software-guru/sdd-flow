import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useChangeRequests } from '../../hooks/use-change-requests';
import PageContainer from '../../components/page-container';
import WorkItemTable from '../../features/work-items/work-item-table';

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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Change Requests</h1>
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
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
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
          className="sdd-select rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
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

      <WorkItemTable
        data={data}
        loading={isLoading}
        baseUrl={`/tenants/${tenantId}/projects/${projectId}/crs`}
        emptyTitle="No change requests"
        emptyDescription={
          status
            ? 'No change requests match the selected filters'
            : 'Create your first change request to get started'
        }
        onPageChange={setPage}
      />
    </PageContainer>
  );
}
