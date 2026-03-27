import { useState, FormEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useBug, useTransitionBug, useUpdateBug } from '../../hooks/useBugs';
import { useComments, useAddComment } from '../../hooks/useComments';
import { useWorkers } from '../../hooks/useWorkers';
import StatusBadge from '../../components/StatusBadge';
import SeverityBadge from '../../components/SeverityBadge';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import MarkdownEditor from '../../components/MarkdownEditor';
import JobOptionsDialog from '../../components/JobOptionsDialog';
import type { BugStatus } from '../../types';

const TRANSITIONS: Record<string, BugStatus[]> = {
  draft: ['open'],
  open: ['in_progress', 'wont_fix'],
  in_progress: ['resolved', 'wont_fix'],
  resolved: ['closed', 'open'],
  wont_fix: ['open'],
  closed: ['open'],
};

const NON_EDITABLE_STATUSES: BugStatus[] = ['closed', 'wont_fix'];

export default function DetailPage() {
  const { tenantId, projectId, bugId } = useParams();
  const navigate = useNavigate();
  const { data: bug, isLoading } = useBug(tenantId, projectId, bugId);
  const { data: comments } = useComments(tenantId, projectId, 'bugs', bugId);
  const { data: workers } = useWorkers(tenantId, projectId);
  const transitionBug = useTransitionBug(tenantId!, projectId!, bugId!);
  const updateBug = useUpdateBug(tenantId!, projectId!, bugId!);
  const addComment = useAddComment(tenantId!, projectId!, 'bugs', bugId!);
  const [commentBody, setCommentBody] = useState('');
  const [showEnrichDialog, setShowEnrichDialog] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');

  const hasOnlineWorker = workers?.some((w) => w.is_online) ?? false;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!bug) {
    return (
      <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
        Bug not found
      </div>
    );
  }

  const availableTransitions = TRANSITIONS[bug.status] || [];
  const canEdit = !NON_EDITABLE_STATUSES.includes(bug.status as BugStatus);

  const startEditing = () => {
    setEditTitle(bug.title);
    setEditBody(bug.body);
    setEditing(true);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    await updateBug.mutateAsync({ title: editTitle, body: editBody });
    setEditing(false);
  };

  const handleTransition = (status: BugStatus) => {
    transitionBug.mutate({ status });
  };

  const handleComment = async (e: FormEvent) => {
    e.preventDefault();
    if (!commentBody.trim()) return;
    await addComment.mutateAsync({ body: commentBody });
    setCommentBody('');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/bugs`}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to Bugs
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
                disabled={updateBug.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {updateBug.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        ) : (
          <>
            <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-700">
              <div className="flex items-start justify-between gap-4">
                <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  <span className="mr-2 font-mono text-base font-normal text-slate-400 dark:text-slate-500">
                    #{bug.formatted_number}
                  </span>
                  {bug.title}
                </h1>
                <div className="flex items-center gap-2">
                  {bug.status === 'draft' && hasOnlineWorker && (
                    <button
                      onClick={() => setShowEnrichDialog(true)}
                      className="inline-flex items-center gap-1.5 rounded-md bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                      </svg>
                      Enrich on Worker
                    </button>
                  )}
                  {canEdit && (
                    <button
                      onClick={startEditing}
                      className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                    >
                      Edit
                    </button>
                  )}
                  <SeverityBadge severity={bug.severity} />
                  <StatusBadge status={bug.status} />
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                <span>Created {new Date(bug.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            <div className="px-6 py-5">
              <MarkdownRenderer content={bug.body} />
            </div>
          </>
        )}

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
                  disabled={transitionBug.isPending}
                  className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                >
                  {status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </button>
              ))}
            </div>
          </div>
        )}

      </div>

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
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-[10px] font-semibold text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                    ?
                  </div>
                  <span className="text-slate-400 dark:text-slate-500">
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

        <form
          onSubmit={handleComment}
          className="border-t border-slate-200 px-6 py-4 dark:border-slate-700"
        >
          <textarea
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            placeholder="Write a comment..."
            rows={3}
            className="markdown-input block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
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

      {showEnrichDialog && (
        <JobOptionsDialog
          tenantId={tenantId!}
          projectId={projectId!}
          jobType="enrich"
          entityType="bug"
          entityId={bugId!}
          onSuccess={(jobId) => {
            setShowEnrichDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowEnrichDialog(false)}
        />
      )}
    </div>
  );
}
