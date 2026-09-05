import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useBugs } from '../../hooks/use-bugs';
import PageContainer from '../../components/page-container';
import WorkItemTable from '../../features/work-items/work-item-table';
import { translate } from '@/i18n';

const STATUS_OPTIONS = [
  {
    value: '',
    get label() {
      return translate('bugs:auto.all_statuses');
    },
  },
  {
    value: 'open',
    get label() {
      return translate('bugs:auto.open');
    },
  },
  {
    value: 'in_progress',
    get label() {
      return translate('bugs:auto.in_progress');
    },
  },
  {
    value: 'resolved',
    get label() {
      return translate('bugs:auto.resolved');
    },
  },
  {
    value: 'wont_fix',
    get label() {
      return translate('bugs:auto.won_t_fix');
    },
  },
  {
    value: 'closed',
    get label() {
      return translate('bugs:auto.closed');
    },
  },
  {
    value: 'deleted',
    get label() {
      return translate('bugs:auto.deleted');
    },
  },
];

const SEVERITY_OPTIONS = [
  {
    value: '',
    get label() {
      return translate('bugs:auto.all_severities');
    },
  },
  {
    value: 'critical',
    get label() {
      return translate('bugs:auto.critical');
    },
  },
  {
    value: 'major',
    get label() {
      return translate('bugs:auto.major');
    },
  },
  {
    value: 'minor',
    get label() {
      return translate('bugs:auto.minor_2');
    },
  },
  {
    value: 'trivial',
    get label() {
      return translate('bugs:auto.trivial');
    },
  },
];

export default function ListPage() {
  const { tenantId, projectId } = useParams();
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useBugs(tenantId, projectId, {
    status: status || undefined,
    severity: severity || undefined,
    page,
    page_size: 20,
  });

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {translate('bugs:auto.bugs_2')}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {translate('bugs:auto.track_and_manage_bugs_for_this_project')}
          </p>
        </div>
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/bugs/new`}
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
          {translate('bugs:auto.report_bug')}
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
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
        <select
          value={severity}
          onChange={(e) => {
            setSeverity(e.target.value);
            setPage(1);
          }}
          className="sdd-select rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
        >
          {SEVERITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {data && (
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {data.total} {translate('bugs:auto.result')}
            {data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <WorkItemTable
        data={data}
        loading={isLoading}
        baseUrl={`/tenants/${tenantId}/projects/${projectId}/bugs`}
        emptyTitle={translate('bugs:auto.no_bugs_found')}
        emptyDescription={
          status || severity
            ? translate('bugs:auto.no_bugs_match_the_selected_filters')
            : translate('bugs:auto.no_bugs_reported_yet')
        }
        onPageChange={setPage}
      />
    </PageContainer>
  );
}
