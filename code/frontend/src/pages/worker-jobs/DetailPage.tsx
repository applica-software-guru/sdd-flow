import { useParams, Link } from 'react-router-dom';
import { useWorkerJob, useWorkerJobStream, useAnswerQuestion, useCancelJob } from '../../hooks/useWorkers';
import JobStatusBadge from '../../components/JobStatusBadge';
import WorkerTerminal from '../../components/WorkerTerminal';
import WorkerQAPanel from '../../components/WorkerQAPanel';

export default function DetailPage() {
  const { tenantId, projectId, jobId } = useParams();

  const { data: job, isLoading } = useWorkerJob(tenantId, projectId, jobId);

  const isLive = job?.status === 'queued' || job?.status === 'assigned' || job?.status === 'running';
  const { messages: streamMessages, isStreaming } = useWorkerJobStream(
    tenantId, projectId, jobId, isLive
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
      <div className="mx-auto max-w-3xl text-center py-16">
        <p className="text-slate-500 dark:text-slate-400">Job not found</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
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
              <span className="text-slate-400 dark:text-slate-500 mr-2">
                {job.entity_type === 'change_request' ? 'CR' : 'Bug'}:
              </span>
              {job.entity_title || 'Job'}
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
    </div>
  );
}
