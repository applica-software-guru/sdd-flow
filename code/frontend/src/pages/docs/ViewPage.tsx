import { useState, useEffect, FormEvent } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useDoc, useUpdateDoc, useDeleteDoc } from '../../hooks/useDocs';
import { useWorkers } from '../../hooks/useWorkers';
import PageContainer from '../../components/PageContainer';
import StatusBadge from '../../components/StatusBadge';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import MarkdownEditor from '../../components/MarkdownEditor';
import ConfirmDialog from '../../components/ConfirmDialog';
import JobOptionsDialog from '../../components/JobOptionsDialog';

function PathBreadcrumb({ path, docsBase }: { path: string; docsBase: string }) {
  const parts = path.split('/').filter(Boolean);
  return (
    <nav className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
      <Link to={docsBase} className="hover:text-blue-600 dark:hover:text-blue-400">
        Docs
      </Link>
      {parts.map((part, i) => {
        const isLast = i === parts.length - 1;
        return (
          <span key={i} className="flex items-center gap-1">
            <svg className="h-3 w-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
            {isLast ? (
              <span className="font-medium text-slate-700 dark:text-slate-200">{part}</span>
            ) : (
              <span>{part}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}

export default function ViewPage() {
  const { tenantId, projectId, docId } = useParams();
  const navigate = useNavigate();

  const docsBase = `/tenants/${tenantId}/projects/${projectId}/docs`;

  const { data: doc, isLoading } = useDoc(tenantId, projectId, docId);
  const updateDoc = useUpdateDoc(tenantId!, projectId!, docId!);
  const deleteDoc = useDeleteDoc(tenantId!, projectId!, docId!);
  const { data: workers } = useWorkers(tenantId, projectId);

  const [editing, setEditing] = useState(false);
  useEffect(() => { setEditing(false); }, [docId]);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEnrichDialog, setShowEnrichDialog] = useState(false);

  const hasOnlineWorker = workers?.some((w) => w.is_online) ?? false;

  // Derive back link folder from doc path
  const backLink = (() => {
    if (!doc) return docsBase;
    const folder = doc.path.split('/').slice(0, -1).join('/');
    return folder ? `${docsBase}?path=${encodeURIComponent(folder)}` : docsBase;
  })();

  const startEditing = () => {
    if (!doc) return;
    setEditTitle(doc.title);
    setEditContent(doc.content);
    setEditStatus(doc.status);
    setEditing(true);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    await updateDoc.mutateAsync({ title: editTitle, content: editContent, status: editStatus });
    setEditing(false);
  };

  const handleDelete = async () => {
    await deleteDoc.mutateAsync();
    navigate(docsBase);
  };

  if (isLoading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center py-24">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      </PageContainer>
    );
  }

  if (!doc) {
    return (
      <PageContainer>
        <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
          Document not found
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      {/* Back link */}
      <div className="mb-4">
        <Link
          to={backLink}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Documentation
        </Link>
      </div>

      {/* Main card */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {/* Card header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <PathBreadcrumb path={doc.path} docsBase={docsBase} />
          {!editing && (
            <div className="flex items-center gap-2">
              {doc.status === 'draft' && hasOnlineWorker && (
                <button
                  onClick={() => setShowEnrichDialog(true)}
                  className="inline-flex items-center gap-1.5 rounded-md bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
                  </svg>
                  Enrich
                </button>
              )}
              <button
                onClick={startEditing}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Edit
              </button>
              <button
                onClick={() => setShowDeleteDialog(true)}
                className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 dark:bg-slate-800 dark:border-red-300"
              >
                Delete
              </button>
            </div>
          )}
        </div>

        {/* Card content */}
        <div className="px-8 py-6">
          {editing ? (
            <form onSubmit={handleSave} className="space-y-4">
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
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value)}
                  className="sdd-select mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
                >
                  <option value="new">New</option>
                  <option value="changed">Changed</option>
                  <option value="synced">Synced</option>
                  <option value="deleted">Deleted</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">Content</label>
                <MarkdownEditor value={editContent} onChange={setEditContent} height={400} />
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
                  disabled={updateDoc.isPending}
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {updateDoc.isPending ? 'Saving…' : 'Save'}
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="mb-6 flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{doc.title}</h1>
                  <p className="mt-1 text-xs text-slate-400">
                    Updated {new Date(doc.updated_at).toLocaleDateString()}
                    {' · '}v{doc.version}
                  </p>
                </div>
                <StatusBadge status={doc.status} />
              </div>

              {doc.content ? (
                <MarkdownRenderer content={doc.content} />
              ) : (
                <p className="text-sm italic text-slate-400">
                  This document has no content yet. Click <strong>Edit</strong> to add content.
                </p>
              )}
            </>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={showDeleteDialog}
        title="Delete document"
        message="Are you sure you want to delete this document? This action cannot be undone."
        variant="danger"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteDialog(false)}
      />

      {showEnrichDialog && (
        <JobOptionsDialog
          tenantId={tenantId!}
          projectId={projectId!}
          jobType="enrich"
          entityType="document"
          entityId={doc.id}
          onSuccess={(jobId) => {
            setShowEnrichDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowEnrichDialog(false)}
        />
      )}
    </PageContainer>
  );
}
