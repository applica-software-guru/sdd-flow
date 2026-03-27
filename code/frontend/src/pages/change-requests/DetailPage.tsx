import { useState, FormEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useChangeRequest, useTransitionCR, useUpdateCR } from '../../hooks/useChangeRequests';
import { useComments, useAddComment } from '../../hooks/useComments';
import { useWorkers } from '../../hooks/useWorkers';
import StatusBadge from '../../components/StatusBadge';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import MarkdownEditor from '../../components/MarkdownEditor';
import JobOptionsDialog from '../../components/JobOptionsDialog';
import type { CRStatus, JobType } from '../../types';

const EDITABLE_STATUSES: CRStatus[] = ['draft', 'pending'];

const TRANSITIONS: Record<string, CRStatus[]> = {
  draft: ['pending', 'rejected'],
  pending: ['rejected', 'draft'],
  rejected: ['draft'],
  applied: ['closed'],
  closed: [],
};

export default function DetailPage() {
  const { tenantId, projectId, crId } = useParams();
  const { data: cr, isLoading } = useChangeRequest(tenantId, projectId, crId);
  const { data: comments } = useComments(tenantId, projectId, 'change-requests', crId);
  const transitionCR = useTransitionCR(tenantId!, projectId!, crId!);
  const addComment = useAddComment(tenantId!, projectId!, 'change-requests', crId!);
  const updateCR = useUpdateCR(tenantId!, projectId!, crId!);
  const { data: workers } = useWorkers(tenantId, projectId);
  const navigate = useNavigate();
  const [commentBody, setCommentBody] = useState('');
  const [jobDialog, setJobDialog] = useState<{ jobType: JobType } | null>(null);
  const hasOnlineWorker = workers?.some((w) => w.is_online) ?? false;
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!cr) {
    return (
      <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
        Change request not found
      </div>
    );
  }

  const availableTransitions = TRANSITIONS[cr.status] || [];

  const handleTransition = (status: CRStatus) => {
    transitionCR.mutate({ status });
  };

  const startEditing = () => {
    setEditTitle(cr.title);
    setEditBody(cr.body);
    setEditing(true);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    await updateCR.mutateAsync({ title: editTitle, body: editBody });
    setEditing(false);
  };

  const handleComment = async (e: FormEvent) => {
    e.preventDefault();
    if (!commentBody.trim()) return;
    await addComment.mutateAsync({ body: commentBody });
    setCommentBody('');
  };

  const canEdit = EDITABLE_STATUSES.includes(cr.status as CRStatus);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/crs`}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to CRs
        </Link>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {editing ? (
          <form onSubmit={handleSave} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Title</label>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Body</label>
              <MarkdownEditor value={editBody} onChange={setEditBody} height={500} />
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updateCR.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {updateCR.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        ) : (
          <>
            <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-700">
              <div className="flex items-start justify-between gap-4">
                <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  <span className="mr-2 font-mono text-base font-normal text-slate-400 dark:text-slate-500">
                    #{cr.formatted_number}
                  </span>
                  {cr.title}
                </h1>
                <div className="flex items-center gap-2">
                  {canEdit && (
                    <button
                      onClick={startEditing}
                      className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                    >
                      Edit
                    </button>
                  )}
                  <StatusBadge status={cr.status} />
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                <span>Created {new Date(cr.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            <div className="px-6 py-5">
              <MarkdownRenderer content={cr.body} />
            </div>
          </>
        )}

        {/* Status transitions */}
        {availableTransitions.length > 0 && (
          <div className="border-t border-slate-200 px-6 py-4 dark:border-slate-700">
            <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">
              Transition to:
            </p>
            <div className="flex flex-wrap gap-2">
              {availableTransitions.map((status) => (
                <button
                  key={status}
                  onClick={() => handleTransition(status)}
                  disabled={transitionCR.isPending}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  {status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Enrich on Worker */}
        {cr.status === 'draft' && hasOnlineWorker && (
          <div className="border-t border-slate-200 px-6 py-4 dark:border-slate-700">
            <button
              onClick={() => setJobDialog({ jobType: 'enrich' })}
              className="inline-flex items-center gap-2 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
              </svg>
              Enrich on Worker
            </button>
          </div>
        )}

      </div>

      {jobDialog && (
        <JobOptionsDialog
          tenantId={tenantId!}
          projectId={projectId!}
          jobType={jobDialog.jobType}
          entityType="change_request"
          entityId={cr.id}
          onSuccess={(jobId) => {
            setJobDialog(null);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setJobDialog(null)}
        />
      )}

      {/* Comments */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">
            Comments ({comments?.length || 0})
          </h2>
        </div>

        {comments && comments.length > 0 ? (
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {comments.map((comment) => (
              <div key={comment.id} className="px-6 py-4">
                <div className="flex items-center gap-2 text-sm">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-[10px] font-semibold text-blue-700">
                    ?
                  </div>
                  <span className="text-slate-400">
                    {new Date(comment.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="mt-2 pl-8">
                  <MarkdownRenderer content={comment.body} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            No comments yet
          </div>
        )}

        {/* Add comment */}
        <form
          onSubmit={handleComment}
          className="border-t border-slate-200 px-6 py-4 dark:border-slate-700"
        >
          <textarea
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            placeholder="Write a comment..."
            rows={3}
            className="markdown-input block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
          />
          <div className="mt-3 flex justify-end">
            <button
              type="submit"
              disabled={addComment.isPending || !commentBody.trim()}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {addComment.isPending ? 'Posting...' : 'Add comment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
