import { useParams, Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useWorkerJob, useWorkerJobStream, useAnswerQuestion, useCancelJob } from '../../hooks/useWorkers';
import JobStatusBadge from '../../components/JobStatusBadge';
import PageContainer from '../../components/PageContainer';
import WorkerTerminal from '../../components/WorkerTerminal';
import WorkerQAPanel from '../../components/WorkerQAPanel';

export default function DetailPage() {
  const { tenantId, projectId, jobId } = useParams();
  const queryClient = useQueryClient();

  const { data: job, isLoading } = useWorkerJob(tenantId, projectId, jobId);

  const isLive = job?.status === 'queued' || job?.status === 'assigned' || job?.status === 'running';
  const { messages: streamMessages, isStreaming } = useWorkerJobStream(
    tenantId,
    projectId,
    jobId,
    isLive,
    () => {
      queryClient.invalidateQueries({
        queryKey: ['tenants', tenantId, 'projects', projectId, 'worker-jobs', jobId],
      });
    },
  );

  const answerMutation = useAnswerQuestion(tenantId!, projectId!, jobId!);
  const cancelMutation = useCancelJob(tenantId!, projectId!, jobId!);

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
        <p className="text-slate-500 dark:text-slate-400">Job not found</p>
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
          &larr; Back to Workers
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {job.entity_type && (
                <span className="text-slate-400 dark:text-slate-500 mr-2">
                  {job.entity_type === 'change_request' ? 'CR' : job.entity_type === 'bug' ? 'Bug' : 'Doc'}:
                </span>
              )}
              {job.job_type === 'build' ? (job.entity_title || 'Project Build')
                : job.job_type === 'custom' ? 'Custom Job'
                : job.entity_title || 'Job'}
            </h1>
            <div className="mt-2 flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
              <JobStatusBadge status={job.status} />
              <span>Agent: {job.agent}</span>
              {job.worker_name && <span>Worker: {job.worker_name}</span>}
              {job.exit_code != null && <span>Exit code: {job.exit_code}</span>}
            </div>
          </div>
          {isLive && (
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              Cancel
            </button>
          )}
        </div>

        {/* Timestamps */}
        <div className="mt-3 flex gap-4 text-xs text-slate-400 dark:text-slate-500">
          <span>Created: {new Date(job.created_at).toLocaleString()}</span>
          {job.started_at && <span>Started: {new Date(job.started_at).toLocaleString()}</span>}
          {job.completed_at && <span>Completed: {new Date(job.completed_at).toLocaleString()}</span>}
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
            Files Changed ({job.changed_files.length})
          </h2>
          <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {job.changed_files.map((file) => (
                  <tr key={file.path} className="flex items-center gap-3 px-4 py-2 font-mono hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="w-20 flex-shrink-0">
                      <span
                        className={
                          file.status === 'new'
                            ? 'rounded px-1.5 py-0.5 text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400'
                            : file.status === 'deleted'
                            ? 'rounded px-1.5 py-0.5 text-xs font-semibold bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
                            : 'rounded px-1.5 py-0.5 text-xs font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400'
                        }
                      >
                        {file.status === 'new' ? 'new' : file.status === 'deleted' ? 'del' : 'mod'}
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
