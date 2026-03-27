import { useMemo, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useDocs, useCreateDoc } from '../../hooks/useDocs';
import StatusBadge from '../../components/StatusBadge';

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor">
      <path d="M1.75 1A1.75 1.75 0 000 2.75v10.5C0 14.216.784 15 1.75 15h12.5A1.75 1.75 0 0016 13.25v-8.5A1.75 1.75 0 0014.25 3H7.5a.25.25 0 01-.2-.1l-.9-1.2C6.07 1.26 5.55 1 5 1H1.75z" />
    </svg>
  );
}

function FileIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor">
      <path d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0113.25 16h-9.5A1.75 1.75 0 012 14.25V1.75zm1.75-.25a.25.25 0 00-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 00.25-.25V6h-2.75A1.75 1.75 0 019 4.25V1.5H3.75zm6.75.062V4.25c0 .138.112.25.25.25h2.688a.252.252 0 00-.011-.013L10.5 1.812z" />
    </svg>
  );
}

export default function TreePage() {
  const { tenantId, projectId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const currentPath = searchParams.get('path') ?? '';

  const docsBase = `/tenants/${tenantId}/projects/${projectId}/docs`;
  const docUrl = (docId: string) => `${docsBase}/${docId}`;

  const { data: docs, isLoading } = useDocs(tenantId, projectId, {});
  const createDoc = useCreateDoc(tenantId!, projectId!);

  // New document inline form
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newPath, setNewPath] = useState('');

  const openNewForm = () => {
    const defaultPath = currentPath ? `${currentPath}/` : '';
    setNewTitle('');
    setNewPath(defaultPath);
    setShowNewForm(true);
  };

  const handleCreateDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newPath.trim()) return;
    const created = await createDoc.mutateAsync({ title: newTitle.trim(), path: newPath.trim(), content: '', status: 'new' });
    navigate(docUrl(created.id));
  };

  // Build the contents of the current folder
  const { subfolders, documents } = useMemo(() => {
    const allDocs = docs ?? [];
    const prefix = currentPath ? currentPath + '/' : '';

    const folderSet = new Set<string>();
    const documents = [];

    for (const doc of allDocs) {
      if (!doc.path.startsWith(prefix)) continue;
      const rest = doc.path.slice(prefix.length);
      const slashIdx = rest.indexOf('/');

      if (slashIdx === -1) {
        documents.push(doc);
      } else {
        folderSet.add(rest.slice(0, slashIdx));
      }
    }

    const subfolders = Array.from(folderSet).sort();
    documents.sort((a, b) => a.path.localeCompare(b.path));

    return { subfolders, documents };
  }, [docs, currentPath]);

  // Breadcrumb parts
  const breadcrumbs = useMemo(() => {
    if (!currentPath) return [];
    return currentPath.split('/').filter(Boolean);
  }, [currentPath]);

  const navigateToFolder = (path: string) => {
    if (path === '') {
      setSearchParams({});
    } else {
      setSearchParams({ path });
    }
  };

  const goUp = () => {
    const parts = currentPath.split('/').filter(Boolean);
    parts.pop();
    navigateToFolder(parts.join('/'));
  };

  return (
    <div className="mx-auto max-w-5xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Documentation</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Browse and manage project documentation files
          </p>
        </div>
        <button
          onClick={openNewForm}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Document
        </button>
      </div>

      {/* New document form */}
      {showNewForm && (
        <form
          onSubmit={handleCreateDoc}
          className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20"
        >
          <p className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">New document</p>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Title"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
              autoFocus
            />
            <input
              type="text"
              placeholder="Path (e.g. product/vision.md)"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100"
            />
            <button
              type="submit"
              disabled={createDoc.isPending || !newTitle.trim() || !newPath.trim()}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createDoc.isPending ? 'Creating…' : 'Create'}
            </button>
            <button
              type="button"
              onClick={() => setShowNewForm(false)}
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Breadcrumb */}
      {breadcrumbs.length > 0 && (
        <nav className="mb-3 flex items-center gap-1 text-sm">
          <button
            onClick={() => navigateToFolder('')}
            className="font-medium text-blue-600 hover:underline dark:text-blue-400"
          >
            Docs
          </button>
          {breadcrumbs.map((part, i) => {
            const isLast = i === breadcrumbs.length - 1;
            const pathUpTo = breadcrumbs.slice(0, i + 1).join('/');
            return (
              <span key={i} className="flex items-center gap-1">
                <span className="text-slate-400">/</span>
                {isLast ? (
                  <span className="font-medium text-slate-700 dark:text-slate-200">{part}</span>
                ) : (
                  <button
                    onClick={() => navigateToFolder(pathUpTo)}
                    className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {part}
                  </button>
                )}
              </span>
            );
          })}
        </nav>
      )}

      {/* Table card */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-700/50">
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
              {/* Go up row */}
              {currentPath && (
                <tr
                  className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/30"
                  onClick={goUp}
                >
                  <td className="px-6 py-3" colSpan={3}>
                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                      <FolderIcon className="h-4 w-4 text-amber-400" />
                      <span className="font-mono">..</span>
                    </div>
                  </td>
                </tr>
              )}

              {/* Subfolders */}
              {subfolders.map((folder) => {
                const fullPath = currentPath ? `${currentPath}/${folder}` : folder;
                return (
                  <tr
                    key={fullPath}
                    className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/30"
                    onClick={() => navigateToFolder(fullPath)}
                  >
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2">
                        <FolderIcon className="h-4 w-4 flex-shrink-0 text-amber-400" />
                        <span className="font-medium text-blue-600 hover:underline dark:text-blue-400">
                          {folder}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-3" />
                    <td className="px-6 py-3" />
                  </tr>
                );
              })}

              {/* Documents */}
              {documents.map((doc) => {
                const filename = doc.path.split('/').pop() ?? doc.path;
                return (
                  <tr
                    key={doc.id}
                    className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/30"
                    onClick={() => navigate(docUrl(doc.id))}
                  >
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2">
                        <FileIcon className="h-4 w-4 flex-shrink-0 text-slate-400" />
                        <span className="font-medium text-blue-600 hover:underline dark:text-blue-400">
                          {doc.title || filename}
                        </span>
                        <span className="text-xs text-slate-400">{filename}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="px-6 py-3 text-right text-xs text-slate-400">
                      {new Date(doc.updated_at).toLocaleDateString()}
                    </td>
                  </tr>
                );
              })}

              {/* Empty state */}
              {subfolders.length === 0 && documents.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-6 py-12 text-center text-sm text-slate-400">
                    {docs?.length === 0
                      ? 'No documents yet. Click "New Document" to get started.'
                      : 'This folder is empty.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
