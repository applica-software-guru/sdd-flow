import { useState, FormEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useDoc, useUpdateDoc, useDeleteDoc } from '../../hooks/useDocs';
import StatusBadge from '../../components/StatusBadge';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import MarkdownEditor from '../../components/MarkdownEditor';
import ConfirmDialog from '../../components/ConfirmDialog';

export default function ViewPage() {
  const { tenantId, projectId, docId } = useParams();
  const navigate = useNavigate();
  const { data: doc, isLoading } = useDoc(tenantId, projectId, docId);
  const updateDoc = useUpdateDoc(tenantId!, projectId!, docId!);
  const deleteDoc = useDeleteDoc(tenantId!, projectId!, docId!);

  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">
        Document not found
      </div>
    );
  }

  const startEditing = () => {
    setEditTitle(doc.title);
    setEditContent(doc.content);
    setEditStatus(doc.status);
    setEditing(true);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    await updateDoc.mutateAsync({
      title: editTitle,
      content: editContent,
      status: editStatus,
    });
    setEditing(false);
  };

  const handleDelete = async () => {
    await deleteDoc.mutateAsync();
    navigate(`/tenants/${tenantId}/projects/${projectId}/docs`);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/docs`}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to Docs
        </Link>
        <div className="flex items-center gap-2">
          {!editing && (
            <>
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

      {editing ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Title
              </label>
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Status
              </label>
              <select
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value)}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
              >
                <option value="new">New</option>
                <option value="changed">Changed</option>
                <option value="synced">Synced</option>
                <option value="deleted">Deleted</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Content
              </label>
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
                {updateDoc.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-700">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  {doc.title}
                </h1>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{doc.path}</p>
              </div>
              <StatusBadge status={doc.status} />
            </div>
            <div className="mt-2 text-xs text-slate-400">
              Updated{' '}
              {new Date(doc.updated_at).toLocaleDateString()}
            </div>
          </div>
          <div className="px-6 py-5">
            {doc.content ? (
              <MarkdownRenderer content={doc.content} />
            ) : (
              <p className="text-sm italic text-slate-400">
                This document has no content yet. Click Edit to add content.
              </p>
            )}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={showDeleteDialog}
        title="Delete document"
        message="Are you sure you want to delete this document? This action cannot be undone."
        variant="danger"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteDialog(false)}
      />
    </div>
  );
}
