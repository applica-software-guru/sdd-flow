import { formatDateTime } from '@/lib/format';
import { useParams, Link } from 'react-router-dom';
import { queryKeys } from '../../api/query-keys';
import { useQueryClient } from '@tanstack/react-query';
import {
  useWorkerJob,
  useWorkerJobStream,
  useAnswerQuestion,
  useCancelJob,
} from '../../hooks/use-workers';
import JobStatusBadge from '../../components/job-status-badge';
import PageContainer from '../../components/page-container';
import WorkerTerminal from '../../components/worker-terminal';
import WorkerQAPanel from '../../components/worker-qa-panel';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

export default function DetailPage() {
  const { tenantId, projectId, jobId } = useParams();
  const queryClient = useQueryClient();

  const { data: job, isLoading } = useWorkerJob(tenantId, projectId, jobId);

  const isLive =
    job?.status === 'queued' || job?.status === 'assigned' || job?.status === 'running';
  const { messages: streamMessages, isStreaming } = useWorkerJobStream(
    tenantId,
    projectId,
    jobId,
    isLive,
    () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.workers.job(tenantId, projectId, jobId),
      });
    }
  );

  const answerMutation = useAnswerQuestion(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(jobId, 'jobId')
  );
  const cancelMutation = useCancelJob(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(jobId, 'jobId')
  );

  // Use stream messages when live, otherwise use the static messages from the job detail
  const messages = isLive ? streamMessages : (job?.messages ?? []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!job) {
    return (
      <PageContainer className="py-16 text-center">
        <p className="text-slate-500 dark:text-slate-400">
          {translate('workers:auto.job_not_found')}
        </p>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* Header */}
      <div className="mb-6">
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/workers`}
          className="mb-2 inline-block text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
        >
          {translate('workers:auto.larr_back_to_workers')}
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {job.entity_type && (
                <span className="mr-2 text-slate-400 dark:text-slate-500">
                  {job.entity_type === 'change_request'
                    ? 'CR'
                    : job.entity_type === 'bug'
                      ? translate('workers:auto.bug_2')
                      : translate('workers:auto.doc')}
                  :
                </span>
              )}
              {job.job_type === 'build'
                ? job.entity_title || translate('common:fallback.projectBuild')
                : job.job_type === 'custom'
                  ? translate('workers:auto.custom_job')
                  : job.entity_title || translate('common:fallback.job')}
            </h1>
            <div className="mt-2 flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
              <JobStatusBadge status={job.status} />
              <span>
                {translate('workers:auto.agent')} {job.agent}
              </span>
              {job.worker_name && (
                <span>
                  {translate('workers:auto.worker_2')} {job.worker_name}
                </span>
              )}
              {job.exit_code != null && (
                <span>
                  {translate('workers:auto.exit_code')} {job.exit_code}
                </span>
              )}
            </div>
          </div>
          {isLive && (
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {translate('workers:auto.cancel')}
            </button>
          )}
        </div>

        {/* Timestamps */}
        <div className="mt-3 flex gap-4 text-xs text-slate-400 dark:text-slate-500">
          <span>
            {translate('workers:auto.created')} {formatDateTime(job.created_at)}
          </span>
          {job.started_at && (
            <span>
              {translate('workers:auto.started')} {formatDateTime(job.started_at)}
            </span>
          )}
          {job.completed_at && (
            <span>
              {translate('workers:auto.completed')} {formatDateTime(job.completed_at)}
            </span>
          )}
        </div>
      </div>

      {/* Terminal */}
      <WorkerTerminal messages={messages} isStreaming={isStreaming && isLive} />

      {/* Q&A Panel */}
      {isLive && (
        <WorkerQAPanel
          messages={messages}
          onAnswer={(content) => answerMutation.mutate(content)}
          isSubmitting={answerMutation.isPending}
        />
      )}

      {/* Files Changed */}
      {!isLive && job.changed_files && job.changed_files.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {translate('workers:auto.files_changed')}
            {job.changed_files.length})
          </h2>
          <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {job.changed_files.map((file) => (
                  <tr
                    key={file.path}
                    className="flex items-center gap-3 px-4 py-2 font-mono hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  >
                    <td className="w-20 flex-shrink-0">
                      <span
                        className={
                          file.status === 'new'
                            ? 'rounded bg-green-100 px-1.5 py-0.5 text-xs font-semibold text-green-700 dark:bg-green-900/40 dark:text-green-400'
                            : file.status === 'deleted'
                              ? 'rounded bg-red-100 px-1.5 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-900/40 dark:text-red-400'
                              : 'rounded bg-amber-100 px-1.5 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/40 dark:text-amber-400'
                        }
                      >
                        {file.status === 'new'
                          ? 'new'
                          : file.status === 'deleted'
                            ? translate('workers:auto.del')
                            : translate('workers:auto.mod')}
                      </span>
                    </td>
                    <td className="flex-1 text-slate-700 dark:text-slate-300">{file.path}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
