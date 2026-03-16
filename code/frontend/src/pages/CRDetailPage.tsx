import { useState, FormEvent } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useChangeRequest, useTransitionCR } from '../hooks/useChangeRequests';
import { useComments, useAddComment } from '../hooks/useComments';
import StatusBadge from '../components/StatusBadge';
import MarkdownRenderer from '../components/MarkdownRenderer';
import type { CRStatus } from '../types';

const TRANSITIONS: Record<string, CRStatus[]> = {
  draft: ['approved', 'rejected'],
  approved: ['applied', 'rejected'],
  rejected: ['draft'],
  applied: ['closed'],
  closed: [],
};

export default function CRDetailPage() {
  const { tenantId, projectId, crId } = useParams();
  const { data: cr, isLoading } = useChangeRequest(tenantId, projectId, crId);
  const { data: comments } = useComments(tenantId, projectId, 'change-requests', crId);
  const transitionCR = useTransitionCR(tenantId!, projectId!, crId!);
  const addComment = useAddComment(tenantId!, projectId!, 'change-requests', crId!);
  const [commentBody, setCommentBody] = useState('');

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
        <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-700">
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">{cr.title}</h1>
            <StatusBadge status={cr.status} />
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
            <span>Created {new Date(cr.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        <div className="px-6 py-5">
          <MarkdownRenderer content={cr.body} />
        </div>

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
            className="block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
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
