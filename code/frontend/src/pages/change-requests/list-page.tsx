import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useChangeRequests } from '../../hooks/use-change-requests';
import PageContainer from '../../components/page-container';
import WorkItemTable from '../../features/work-items/work-item-table';
import { translate } from '@/i18n';

const STATUS_OPTIONS = [
  {
    value: '',
    get label() {
      return translate('change-requests:auto.all_statuses');
    },
  },
  {
    value: 'draft',
    get label() {
      return translate('change-requests:auto.draft_2');
    },
  },
  {
    value: 'pending',
    get label() {
      return translate('change-requests:auto.pending');
    },
  },
  {
    value: 'rejected',
    get label() {
      return translate('change-requests:auto.rejected');
    },
  },
  {
    value: 'applied',
    get label() {
      return translate('change-requests:auto.applied');
    },
  },
  {
    value: 'closed',
    get label() {
      return translate('change-requests:auto.closed');
    },
  },
  {
    value: 'deleted',
    get label() {
      return translate('change-requests:auto.deleted');
    },
  },
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
            {translate('change-requests:auto.change_requests_2')}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {translate('change-requests:auto.track_and_manage_change_requests_for_this')}
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
          {translate('change-requests:auto.new_cr')}
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
            {data.total} {translate('change-requests:auto.result')}
            {data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <WorkItemTable
        data={data}
        loading={isLoading}
        baseUrl={`/tenants/${tenantId}/projects/${projectId}/crs`}
        emptyTitle={translate('change-requests:auto.no_change_requests')}
        emptyDescription={
          status
            ? translate('change-requests:auto.no_change_requests_match_the_selected_filters')
            : translate('change-requests:auto.create_your_first_change_request_to_get')
        }
        onPageChange={setPage}
      />
    </PageContainer>
  );
}
