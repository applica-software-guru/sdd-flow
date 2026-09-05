import { formatDateOnly } from '@/lib/format';
import { useState, useMemo, useRef, FormEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  useChangeRequest,
  useTransitionCR,
  useUpdateCR,
  useAssignCR,
  useCRAssignments,
} from '../../hooks/use-change-requests';
import { useComments, useAddComment } from '../../hooks/use-comments';
import { useWorkers } from '../../hooks/use-workers';
import { useDocs } from '../../hooks/use-docs';
import { useTenantMembers } from '../../hooks/use-tenants';
import PageContainer from '../../components/page-container';
import StatusBadge from '../../components/status-badge';
import MarkdownRenderer from '../../components/markdown-renderer';
import MarkdownEditor from '../../components/markdown-editor';
import JobOptionsDialog from '../../components/job-options-dialog';
import ScrollToCommentsButton from '../../components/scroll-to-comments-button';
import CommentsSection from '../../features/work-items/comments-section';
import WorkItemWorkflow from '../../features/work-items/work-item-workflow';
import type { CRStatus, JobType } from '../../types';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

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
  const transitionCR = useTransitionCR(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(crId, 'crId')
  );
  const addComment = useAddComment(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    'change-requests',
    requireRouteParam(crId, 'crId')
  );
  const updateCR = useUpdateCR(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(crId, 'crId')
  );
  const assignCR = useAssignCR(
    requireRouteParam(tenantId, 'tenantId'),
    requireRouteParam(projectId, 'projectId'),
    requireRouteParam(crId, 'crId')
  );
  const { data: members } = useTenantMembers(tenantId);
  const { data: assignmentHistory } = useCRAssignments(tenantId, projectId, crId);
  const { data: workers } = useWorkers(tenantId, projectId);
  const { data: docsData } = useDocs(tenantId, projectId);
  const docs = useMemo(() => docsData ?? [], [docsData]);
  const docsRouteBase = `/tenants/${tenantId}/projects/${projectId}/docs`;
  const navigate = useNavigate();
  const commentsSectionRef = useRef<HTMLDivElement>(null);
  const commentInputRef = useRef<HTMLTextAreaElement>(null);
  const [jobDialog, setJobDialog] = useState<{ jobType: JobType } | null>(null);
  const hasOnlineWorker = workers?.some((w) => w.is_online) ?? false;
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editSlug, setEditSlug] = useState('');

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
        {translate('change-requests:auto.change_request_not_found')}
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
    setEditSlug(cr.slug);
    setEditing(true);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    await updateCR.mutateAsync({
      title: editTitle,
      body: editBody,
      slug: editSlug !== cr.slug ? editSlug : undefined,
    });
    setEditing(false);
  };

  const canEdit = EDITABLE_STATUSES.includes(cr.status as CRStatus);

  return (
    <PageContainer className="space-y-6">
      <div>
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/crs`}
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
          {translate('change-requests:auto.back_to_crs')}
        </Link>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {editing ? (
          <form onSubmit={handleSave} className="space-y-4 p-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {translate('change-requests:auto.title')}
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
                {translate('change-requests:auto.slug')}
              </label>
              <input
                type="text"
                value={editSlug}
                onChange={(e) => setEditSlug(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              />
              <p className="mt-1 text-xs text-slate-400">
                {translate('change-requests:auto.filename')}{' '}
                <code>
                  {translate('change-requests:auto.change_requests')}
                  {cr.formatted_number}-{editSlug}
                  {translate('change-requests:auto.md')}
                </code>
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                {translate('change-requests:auto.body')}
              </label>
              <MarkdownEditor value={editBody} onChange={setEditBody} height={500} />
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                {translate('change-requests:auto.cancel')}
              </button>
              <button
                type="submit"
                disabled={updateCR.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {updateCR.isPending
                  ? translate('change-requests:auto.saving')
                  : translate('change-requests:auto.save')}
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
                      {translate('change-requests:auto.edit')}
                    </button>
                  )}
                  <StatusBadge status={cr.status} />
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                <span>
                  {translate('change-requests:auto.created')} {formatDateOnly(cr.created_at)}
                </span>
              </div>
            </div>

            <div className="px-6 py-5">
              <MarkdownRenderer
                content={cr.body}
                basePath="change-requests"
                docs={docs}
                docsRouteBase={docsRouteBase}
              />
            </div>
          </>
        )}

        <WorkItemWorkflow
          title={cr.title}
          author={cr.author}
          assignee={cr.assignee}
          assigneeId={cr.assignee_id ?? null}
          members={members ?? []}
          history={assignmentHistory}
          transitions={availableTransitions}
          pending={transitionCR.isPending}
          assigning={assignCR.isPending}
          onTransition={handleTransition}
          onAssign={(assigneeId) => assignCR.mutate({ assignee_id: assigneeId })}
        />

        {/* Enrich on Worker */}
        {cr.status === 'draft' && hasOnlineWorker && (
          <div className="border-t border-slate-200 px-6 py-4 dark:border-slate-700">
            <button
              onClick={() => setJobDialog({ jobType: 'enrich' })}
              className="inline-flex items-center gap-2 rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
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
                  d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z"
                />
              </svg>
              {translate('change-requests:auto.enrich_on_worker')}
            </button>
          </div>
        )}
      </div>

      {jobDialog && (
        <JobOptionsDialog
          tenantId={requireRouteParam(tenantId, 'tenantId')}
          projectId={requireRouteParam(projectId, 'projectId')}
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

      <CommentsSection
        comments={comments}
        basePath="change-requests"
        docs={docs}
        docsRouteBase={docsRouteBase}
        sectionRef={commentsSectionRef}
        inputRef={commentInputRef}
        submitting={addComment.isPending}
        onSubmit={async (body) => {
          await addComment.mutateAsync({ body });
        }}
      />
      <ScrollToCommentsButton
        targetRef={commentsSectionRef}
        commentCount={comments?.length || 0}
        inputRef={commentInputRef}
      />
    </PageContainer>
  );
}
