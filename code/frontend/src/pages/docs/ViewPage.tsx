import { useState, useEffect, FormEvent } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useDocs, useDoc, useUpdateDoc, useDeleteDoc, useCreateDoc } from '../../hooks/useDocs';
import { useWorkers } from '../../hooks/useWorkers';
import StatusBadge from '../../components/StatusBadge';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import MarkdownEditor from '../../components/MarkdownEditor';
import ConfirmDialog from '../../components/ConfirmDialog';
import JobOptionsDialog from '../../components/JobOptionsDialog';
import DocFileTree from '../../components/DocFileTree';

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
  const docUrl = (id: string) => `${docsBase}/${id}`;

  const { data: docs } = useDocs(tenantId, projectId, {});
  const { data: doc, isLoading } = useDoc(tenantId, projectId, docId);
  const updateDoc = useUpdateDoc(tenantId!, projectId!, docId!);
  const deleteDoc = useDeleteDoc(tenantId!, projectId!, docId!);
  const createDoc = useCreateDoc(tenantId!, projectId!);
  const { data: workers } = useWorkers(tenantId, projectId);

  const [editing, setEditing] = useState(false);

  // Reset edit mode when navigating to a different document
  useEffect(() => { setEditing(false); }, [docId]);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showEnrichDialog, setShowEnrichDialog] = useState(false);

  const hasOnlineWorker = workers?.some((w) => w.is_online) ?? false;

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

  const handleCreateDoc = async (title: string, path: string) => {
    const created = await createDoc.mutateAsync({ title, path, content: '', status: 'new' });
    navigate(docUrl(created.id));
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      {/* ── File tree sidebar ── */}
      <div className="flex w-60 flex-shrink-0 flex-col border-r border-slate-200 dark:border-slate-700">
        <div className="flex h-12 flex-shrink-0 items-center border-b border-slate-200 px-3 dark:border-slate-700">
          <Link
            to={docsBase}
            className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            Documentation
          </Link>
        </div>

        <DocFileTree
          docs={docs ?? []}
          activeDocId={docId}
          docUrl={docUrl}
          onCreateDoc={handleCreateDoc}
          isCreating={createDoc.isPending}
        />
      </div>

      {/* ── Content area ── */}
      <div className="flex flex-1 flex-col overflow-y-auto">
        {isLoading ? (
          <div className="flex flex-1 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : !doc ? (
          <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
            Document not found
          </div>
        ) : (
          <>
            {/* Breadcrumb + actions bar */}
            <div className="flex h-12 flex-shrink-0 items-center justify-between border-b border-slate-200 px-6 dark:border-slate-700">
              <PathBreadcrumb path={doc.path} docsBase={docsBase} />
              <div className="flex items-center gap-2">
                {!editing && (
                  <>
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
                  </>
                )}
              </div>
            </div>

            {/* Document content */}
            <div className="flex-1 px-8 py-6">
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
          </>
        )}
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
          entityId={doc!.id}
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
