import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useSearch } from '../hooks/useSearch';

export default function SearchModal() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const { tenantId } = useParams();
  const navigate = useNavigate();
  const { data: results, isLoading } = useSearch(tenantId, query);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setOpen(false);
      }
    },
    []
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (!open) {
      setQuery('');
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      <div
        className="fixed inset-0 bg-black/50"
        onClick={() => setOpen(false)}
      />
      <div className="relative z-50 w-full max-w-lg rounded-xl bg-white shadow-2xl dark:bg-slate-800">
        <div className="flex items-center border-b border-slate-200 px-4 dark:border-slate-700">
          <svg
            className="h-5 w-5 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search projects, CRs, bugs, docs..."
            className="flex-1 border-0 bg-transparent px-4 py-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-0 dark:text-slate-100 dark:placeholder-slate-500"
            autoFocus
          />
          <kbd className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500 dark:bg-slate-700 dark:text-slate-400">
            Esc
          </kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {isLoading && query.length >= 2 && (
            <div className="flex items-center justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
            </div>
          )}
          {!isLoading && results && results.length === 0 && query.length >= 2 && (
            <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
              No results found for &ldquo;{query}&rdquo;
            </div>
          )}
          {query.length < 2 && (
            <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
              Type at least 2 characters to search
            </div>
          )}
          {results?.map((result) => (
            <button
              key={`${result.type}-${result.id}`}
              onClick={() => {
                navigate(result.url);
                setOpen(false);
              }}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-700"
            >
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 capitalize dark:bg-slate-700 dark:text-slate-400">
                {result.type.replace('_', ' ')}
              </span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                  {result.title}
                </div>
                {result.snippet && (
                  <div className="truncate text-xs text-slate-500 dark:text-slate-400">
                    {result.snippet}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
