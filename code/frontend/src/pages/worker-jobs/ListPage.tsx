import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useWorkerJobs, useWorkers } from '../../hooks/useWorkers';
import JobStatusBadge from '../../components/JobStatusBadge';
import WorkerStatusBadge from '../../components/WorkerStatusBadge';
import Pagination from '../../components/Pagination';
import EmptyState from '../../components/EmptyState';
import JobOptionsDialog from '../../components/JobOptionsDialog';

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'queued', label: 'Queued' },
  { value: 'assigned', label: 'Assigned' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

export default function ListPage() {
  const { tenantId, projectId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [showSyncDialog, setShowSyncDialog] = useState(false);

  const { data: workers } = useWorkers(tenantId, projectId);
  const { data, isLoading } = useWorkerJobs(tenantId, projectId, {
    status: status || undefined,
    page,
    page_size: 20,
  });

  const onlineWorkers = workers?.filter((w) => w.is_online) ?? [];

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Workers</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Remote workers and job execution history
          </p>
        </div>
        {onlineWorkers.length > 0 && (
          <button
            onClick={() => setShowSyncDialog(true)}
            className="inline-flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            Sync on Worker
          </button>
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
                <WorkerStatusBadge status={worker.is_online ? (worker.status === 'busy' ? 'busy' : 'online') : 'offline'} />
              </div>
              <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                Agent: {worker.agent}
                {worker.branch && (
                  <span className="ml-2">
                    Branch: <code className="font-mono">{worker.branch}</code>
                  </span>
                )}
              </div>
              {worker.last_heartbeat_at && (
                <div className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  Last seen: {new Date(worker.last_heartbeat_at).toLocaleString()}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {workers && workers.length === 0 && (
        <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No workers registered. Run <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs dark:bg-slate-700">sdd remote worker</code> to connect a worker.
          </p>
        </div>
      )}

      {/* Jobs */}
      <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">Jobs</h2>

      <div className="mb-4 flex items-center gap-3">
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="sdd-select rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {data && (
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {data.total} result{data.total !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {showSyncDialog && (
        <JobOptionsDialog
          tenantId={tenantId!}
          projectId={projectId!}
          jobType="sync"
          onSuccess={(jobId) => {
            setShowSyncDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowSyncDialog(false)}
        />
      )}

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No jobs"
            description={
              status
                ? 'No jobs match the selected filter'
                : 'Jobs will appear here when you apply a CR or bug on a worker'
            }
          />
        ) : (
          <>
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-700/50">
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Entity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Status</th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 sm:table-cell dark:text-slate-400">Worker</th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 md:table-cell dark:text-slate-400">Agent</th>
                  <th className="hidden px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 lg:table-cell dark:text-slate-400">Created</th>
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
                            {job.entity_type === 'change_request' ? 'CR' : job.entity_type === 'bug' ? 'Bug' : 'Doc'}
                          </span>
                        )}
                        {job.job_type === 'sync' && !job.entity_title
                          ? 'Project Sync'
                          : job.entity_title || (job.entity_id ? job.entity_id.slice(0, 8) : 'Sync')}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <JobStatusBadge status={job.status} />
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 sm:table-cell dark:text-slate-400">
                      {job.worker_name || '--'}
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 md:table-cell dark:text-slate-400">
                      {job.agent}
                    </td>
                    <td className="hidden px-6 py-4 text-sm text-slate-500 lg:table-cell dark:text-slate-400">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Pagination page={data.page} totalPages={data.pages} onPageChange={setPage} />
          </>
        )}
      </div>
    </div>
  );
}
