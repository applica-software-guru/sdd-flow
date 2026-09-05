import { useState, useMemo, useRef, FormEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  useBug,
  useTransitionBug,
  useUpdateBug,
  useAssignBug,
  useBugAssignments,
} from '../../hooks/use-bugs';
import { useComments, useAddComment } from '../../hooks/use-comments';
import { useWorkers } from '../../hooks/use-workers';
import { useDocs } from '../../hooks/use-docs';
import { useTenantMembers } from '../../hooks/use-tenants';
import PageContainer from '../../components/page-container';
import StatusBadge from '../../components/status-badge';
import SeverityBadge from '../../components/severity-badge';
import MarkdownRenderer from '../../components/markdown-renderer';
import MarkdownEditor from '../../components/markdown-editor';
import JobOptionsDialog from '../../components/job-options-dialog';
import ScrollToCommentsButton from '../../components/scroll-to-comments-button';
import CommentsSection from '../../features/work-items/comments-section';
import WorkItemWorkflow from '../../features/work-items/work-item-workflow';
import type { BugStatus } from '../../types';
import { requireRouteParam } from '@/lib/route-params';

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
  const { data: docsData } = useDocs(tenantId, projectId);
  const docs = useMemo(() => docsData ?? [], [docsData]);
  const docsRouteBase = `/tenants/${tenantId}/projects/${projectId}/docs`;
  const transitionBug = useTransitionBug(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(bugId, 'bugId')
  );
  const updateBug = useUpdateBug(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(bugId, 'bugId')
  );
  const assignBug = useAssignBug(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(bugId, 'bugId')
  );
  const { data: members } = useTenantMembers(tenantId);
  const { data: assignmentHistory } = useBugAssignments(tenantId, projectId, bugId);
  const addComment = useAddComment(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    'bugs',
    requireRouteParam(bugId, 'bugId')
  );
  const commentsSectionRef = useRef<HTMLDivElement>(null);
  const commentInputRef = useRef<HTMLTextAreaElement>(null);
  const [showEnrichDialog, setShowEnrichDialog] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editSlug, setEditSlug] = useState('');

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
    setEditSlug(bug.slug);
    setEditing(true);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    await updateBug.mutateAsync({
      title: editTitle,
      body: editBody,
      slug: editSlug !== bug.slug ? editSlug : undefined,
    });
    setEditing(false);
  };

  const handleTransition = (status: BugStatus) => {
    transitionBug.mutate({ status });
  };

  return (
    <PageContainer className="space-y-6">
      <div>
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/bugs`}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
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
              d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
            />
          </svg>
          Back to Bugs
        </Link>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {editing ? (
          <form onSubmit={handleSave} className="space-y-4 p-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Title
              </label>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Slug
              </label>
              <input
                type="text"
                value={editSlug}
                onChange={(e) => setEditSlug(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              />
              <p className="mt-1 text-xs text-slate-400">
                Filename:{' '}
                <code>
                  bugs/{bug.formatted_number}-{editSlug}.md
                </code>
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Body
              </label>
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
                      <svg
                        className="h-3.5 w-3.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z"
                        />
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
              <MarkdownRenderer
                content={bug.body}
                basePath="bugs"
                docs={docs}
                docsRouteBase={docsRouteBase}
              />
            </div>
          </>
        )}

        <WorkItemWorkflow
          title={bug.title}
          author={bug.author}
          assigneeId={bug.assignee_id ?? null}
          members={members ?? []}
          history={assignmentHistory}
          transitions={availableTransitions}
          pending={transitionBug.isPending}
          assigning={assignBug.isPending}
          onTransition={handleTransition}
          onAssign={(assigneeId) => assignBug.mutate({ assignee_id: assigneeId })}
        />
      </div>

      <CommentsSection
        comments={comments}
        basePath="bugs"
        docs={docs}
        docsRouteBase={docsRouteBase}
        sectionRef={commentsSectionRef}
        inputRef={commentInputRef}
        submitting={addComment.isPending}
        onSubmit={async (body) => {
          await addComment.mutateAsync({ body });
        }}
      />

      {showEnrichDialog && (
        <JobOptionsDialog
          tenantId={requireRouteParam(tenantId, 'tenantId')}
          projectId={requireRouteParam(projectId, 'projectId')}
          jobType="enrich"
          entityType="bug"
          entityId={requireRouteParam(bugId, 'bugId')}
          onSuccess={(jobId) => {
            setShowEnrichDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowEnrichDialog(false)}
        />
      )}
      <ScrollToCommentsButton
        targetRef={commentsSectionRef}
        commentCount={comments?.length || 0}
        inputRef={commentInputRef}
      />
    </PageContainer>
  );
}
