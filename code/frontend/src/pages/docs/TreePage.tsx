import { useMemo, useState, FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useDocs, useCreateDoc } from '../../hooks/useDocs';
import StatusBadge from '../../components/StatusBadge';
import EmptyState from '../../components/EmptyState';

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'new', label: 'New' },
  { value: 'changed', label: 'Changed' },
  { value: 'synced', label: 'Synced' },
  { value: 'deleted', label: 'Deleted' },
];

function getFolderPath(path: string) {
  const parts = path.split('/').filter(Boolean);
  if (parts.length <= 1) {
    return '';
  }

  return parts.slice(0, -1).join('/');
}

function getFolderLabel(path: string) {
  return getFolderPath(path) || 'Root';
}

export default function TreePage() {
  const { tenantId, projectId } = useParams();
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newPath, setNewPath] = useState('');
  const [collapsedFolders, setCollapsedFolders] = useState<Record<string, boolean>>({});
  const { data: docs, isLoading } = useDocs(tenantId, projectId, {
    status: status || undefined,
  });
  const createDoc = useCreateDoc(tenantId!, projectId!);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await createDoc.mutateAsync({
      title: newTitle,
      path: newPath,
      content: '',
      status: 'new',
    });
    setNewTitle('');
    setNewPath('');
    setShowCreateForm(false);
  };

  const filteredDocs = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return [...(docs || [])]
      .filter((doc) => {
        if (!normalizedSearch) {
          return true;
        }

        return [doc.title, doc.path]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(normalizedSearch));
      })
      .sort((a, b) => a.path.localeCompare(b.path));
  }, [docs, search]);

  const groupedDocs = useMemo(() => {
    const groups = new Map<string, typeof filteredDocs>();

    filteredDocs.forEach((doc) => {
      const folder = getFolderLabel(doc.path);
      const existing = groups.get(folder);

      if (existing) {
        existing.push(doc);
      } else {
        groups.set(folder, [doc]);
      }
    });

    return Array.from(groups.entries())
      .sort(([left], [right]) => {
        if (left === 'Root') {
          return -1;
        }
        if (right === 'Root') {
          return 1;
        }
        return left.localeCompare(right);
      })
      .map(([folder, items]) => ({ folder, items }));
  }, [filteredDocs]);

  const toggleFolder = (folder: string) => {
    setCollapsedFolders((current) => ({
      ...current,
      [folder]: !current[folder],
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Documentation</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Project documentation and guides
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
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
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          New Document
        </button>
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title or path"
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 sm:flex-1"
        />
        <div className="flex items-center gap-3 sm:flex-shrink-0">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="sdd-select rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          {docs && (
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {filteredDocs.length} of {docs.length} document{docs.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {showCreateForm && (
        <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
            Create New Document
          </h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Title
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  placeholder="Getting Started"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Path
                </label>
                <input
                  type="text"
                  required
                  value={newPath}
                  onChange={(e) => setNewPath(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  placeholder="guides/getting-started"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createDoc.isPending}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {createDoc.isPending ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      {filteredDocs.length === 0 ? (
        <EmptyState
          title={docs?.length ? 'No matching documents' : 'No documents yet'}
          description={
            docs?.length
              ? 'Try a different search term or status filter.'
              : 'Create your first document to start building your knowledge base'
          }
          icon={
            <svg
              className="h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
              />
            </svg>
          }
        />
      ) : (
        <div className="space-y-4">
          {groupedDocs.map(({ folder, items }) => {
            const isCollapsed = !search.trim() && collapsedFolders[folder];

            return (
              <section
                key={folder}
                className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800"
              >
                <button
                  type="button"
                  onClick={() => toggleFolder(folder)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {folder}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {items.length} document{items.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <svg
                    className={`h-4 w-4 flex-shrink-0 text-slate-400 transition-transform ${isCollapsed ? '-rotate-90' : 'rotate-0'}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19.5 8.25L12 15.75 4.5 8.25"
                    />
                  </svg>
                </button>

                {!isCollapsed && (
                  <div className="divide-y divide-slate-100 dark:divide-slate-700">
                    {items.map((doc) => (
                      <Link
                        key={doc.id}
                        to={`/tenants/${tenantId}/projects/${projectId}/docs/${doc.id}`}
                        className="flex items-center justify-between px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-700"
                      >
                        <div className="min-w-0 flex items-center gap-3">
                          <svg
                            className="h-5 w-5 flex-shrink-0 text-slate-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={1.5}
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                            />
                          </svg>
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                              {doc.title}
                            </p>
                            <p className="truncate text-xs text-slate-500 dark:text-slate-400">
                              {doc.path}
                            </p>
                          </div>
                        </div>
                        <div className="ml-4 flex flex-shrink-0 items-center gap-3">
                          <StatusBadge status={doc.status} />
                          <span className="text-xs text-slate-400">
                            {new Date(doc.updated_at).toLocaleDateString()}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
