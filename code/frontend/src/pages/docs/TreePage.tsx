import { useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useDocs, useCreateDoc } from '../../hooks/useDocs';
import DocFileTree from '../../components/DocFileTree';
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

  const handleCreateDoc = async (title: string, path: string) => {
    const created = await createDoc.mutateAsync({ title, path, content: '', status: 'new' });
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
        // Direct child document
        documents.push(doc);
      } else {
        // Child folder
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
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
      {/* ── File tree sidebar ── */}
      <div className="flex w-56 flex-shrink-0 flex-col border-r border-slate-200 dark:border-slate-700">
        <div className="flex h-12 flex-shrink-0 items-center border-b border-slate-200 px-3 dark:border-slate-700">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Files
          </span>
        </div>

        {isLoading ? (
          <div className="flex flex-1 items-center justify-center">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        ) : (
          <DocFileTree
            docs={docs ?? []}
            docUrl={docUrl}
            onCreateDoc={handleCreateDoc}
            isCreating={createDoc.isPending}
            activeFolderPath={currentPath}
            onFolderClick={navigateToFolder}
          />
        )}
      </div>

      {/* ── Content area: folder browser ── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Breadcrumb bar */}
        <div className="flex h-12 flex-shrink-0 items-center gap-1 border-b border-slate-200 px-4 dark:border-slate-700">
          <button
            onClick={() => navigateToFolder('')}
            className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
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
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{part}</span>
                ) : (
                  <button
                    onClick={() => navigateToFolder(pathUpTo)}
                    className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {part}
                  </button>
                )}
              </span>
            );
          })}
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : (
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 dark:text-slate-400">Name</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 dark:text-slate-400">Status</th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500 dark:text-slate-400">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                {/* Go up row */}
                {currentPath && (
                  <tr
                    className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/30"
                    onClick={goUp}
                  >
                    <td className="px-4 py-2" colSpan={3}>
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
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          <FolderIcon className="h-4 w-4 flex-shrink-0 text-amber-400" />
                          <span className="font-medium text-blue-600 hover:underline dark:text-blue-400">
                            {folder}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-2" />
                      <td className="px-4 py-2" />
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
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          <FileIcon className="h-4 w-4 flex-shrink-0 text-slate-400" />
                          <span className="font-medium text-blue-600 hover:underline dark:text-blue-400">
                            {doc.title || filename}
                          </span>
                          <span className="text-xs text-slate-400">{filename}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2">
                        <StatusBadge status={doc.status} />
                      </td>
                      <td className="px-4 py-2 text-right text-xs text-slate-400">
                        {new Date(doc.updated_at).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}

                {/* Empty state */}
                {subfolders.length === 0 && documents.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-12 text-center text-sm text-slate-400">
                      {docs?.length === 0
                        ? 'No documents yet. Use "+ New document" in the sidebar to get started.'
                        : 'This folder is empty.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
