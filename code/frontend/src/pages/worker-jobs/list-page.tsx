import { formatDateTime } from '@/lib/format';
import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useWorkerJobs, useWorkers } from '../../hooks/use-workers';
import PageContainer from '../../components/page-container';
import JobStatusBadge from '../../components/job-status-badge';
import WorkerStatusBadge from '../../components/worker-status-badge';
import Pagination from '../../components/pagination';
import EmptyState from '../../components/empty-state';
import JobOptionsDialog from '../../components/job-options-dialog';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

const STATUS_OPTIONS = [
  {
    value: '',
    get label() {
      return translate('workers:auto.all_statuses');
    },
  },
  {
    value: 'queued',
    get label() {
      return translate('workers:auto.queued');
    },
  },
  {
    value: 'assigned',
    get label() {
      return translate('workers:auto.assigned');
    },
  },
  {
    value: 'running',
    get label() {
      return translate('workers:auto.running');
    },
  },
  {
    value: 'completed',
    get label() {
      return translate('workers:auto.completed_2');
    },
  },
  {
    value: 'failed',
    get label() {
      return translate('workers:auto.failed');
    },
  },
  {
    value: 'cancelled',
    get label() {
      return translate('workers:auto.cancelled');
    },
  },
];

export default function ListPage() {
  const { tenantId, projectId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [showBuildDialog, setShowBuildDialog] = useState(false);
  const [showCustomDialog, setShowCustomDialog] = useState(false);

  const { data: workers } = useWorkers(tenantId, projectId);
  const { data, isLoading } = useWorkerJobs(tenantId, projectId, {
    status: status || undefined,
    page,
    page_size: 20,
  });

  const onlineWorkers = workers?.filter((w) => w.is_online) ?? [];

  return (
    <PageContainer>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {translate('workers:auto.workers')}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {translate('workers:auto.remote_workers_and_job_execution_history')}
          </p>
        </div>
        {onlineWorkers.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCustomDialog(true)}
              className="inline-flex items-center gap-2 rounded-md bg-slate-600 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
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
                  d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z"
                />
              </svg>
              {translate('workers:auto.custom_job')}
            </button>
            <button
              onClick={() => setShowBuildDialog(true)}
              className="inline-flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
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
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                />
              </svg>
              {translate('workers:auto.build_on_worker')}
            </button>
          </div>
        )}
      </div>

      {/* Worker status cards */}
      {workers && workers.length > 0 && (
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workers.map((worker) => (
            <div
              key={worker.id}
              className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                  {worker.name}
                </span>
                <WorkerStatusBadge
                  status={
                    worker.is_online ? (worker.status === 'busy' ? 'busy' : 'online') : 'offline'
                  }
                />
              </div>
              <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                {translate('workers:auto.agent')} {worker.agent}
                {worker.branch && (
                  <span className="ml-2">
                    {translate('workers:auto.branch')}
                    <code className="font-mono">{worker.branch}</code>
                  </span>
                )}
              </div>
              {worker.last_heartbeat_at && (
                <div className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  {translate('workers:auto.last_seen')} {formatDateTime(worker.last_heartbeat_at)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {workers && workers.length === 0 && (
        <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {translate('workers:auto.no_workers_registered_run')}{' '}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs dark:bg-slate-700">
              {translate('workers:auto.sdd_remote_worker')}
            </code>{' '}
            {translate('workers:auto.to_connect_a_worker')}
          </p>
        </div>
      )}

      {/* Jobs */}
      <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
        {translate('workers:auto.jobs')}
      </h2>

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
            {data.total} {translate('workers:auto.result')}
            {data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {showBuildDialog && (
        <JobOptionsDialog
          tenantId={requireRouteParam(tenantId, 'tenantId')}
          projectId={requireRouteParam(projectId, 'projectId')}
          jobType="build"
          onSuccess={(jobId) => {
            setShowBuildDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowBuildDialog(false)}
        />
      )}

      {showCustomDialog && (
        <JobOptionsDialog
          tenantId={requireRouteParam(tenantId, 'tenantId')}
          projectId={requireRouteParam(projectId, 'projectId')}
          jobType="custom"
          onSuccess={(jobId) => {
            setShowCustomDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowCustomDialog(false)}
        />
      )}

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title={translate('workers:auto.no_jobs')}
            description={
              status
                ? translate('workers:auto.no_jobs_match_the_selected_filter')
                : translate('workers:auto.jobs_will_appear_here_when_you_apply')
            }
          />
        ) : (
          <>
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {translate('workers:auto.entity')}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {translate('workers:auto.status')}
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 sm:table-cell">
                    {translate('workers:auto.worker')}
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 md:table-cell">
                    {translate('workers:auto.agent_2')}
                  </th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 lg:table-cell">
                    {translate('workers:auto.created_2')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data.items.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50 dark:hover:bg-slate-700">
                    <td className="px-6 py-4">
                      <Link
                        to={`/tenants/${tenantId}/projects/${projectId}/workers/${job.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        {job.entity_type && (
                          <span className="mr-1.5 text-xs text-slate-400 dark:text-slate-500">
                            {job.entity_type === 'change_request'
                              ? 'CR'
                              : job.entity_type === 'bug'
                                ? translate('workers:auto.bug_2')
                                : translate('workers:auto.doc')}
                          </span>
                        )}
                        {job.job_type === 'build'
                          ? job.entity_title || translate('common:fallback.projectBuild')
                          : job.job_type === 'custom'
                            ? translate('workers:auto.custom_job')
                            : job.entity_title ||
                              (job.entity_id ? job.entity_id.slice(0, 8) : job.job_type)}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <JobStatusBadge status={job.status} />
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 dark:text-slate-400 sm:table-cell">
                      {job.worker_name || '--'}
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 dark:text-slate-400 md:table-cell">
                      {job.agent}
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 dark:text-slate-400 lg:table-cell">
                      {formatDateTime(job.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination page={data.page} totalPages={data.pages} onPageChange={setPage} />
          </>
        )}
      </div>
    </PageContainer>
  );
}
