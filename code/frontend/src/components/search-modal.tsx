import { useCallback, useEffect, useState } from 'react';
import {
  Bug,
  Clock,
  FileText,
  Folder,
  GitPullRequest,
  Search,
  type LucideIcon,
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import LoadingState from '@/components/shared/loading-state';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog';
import { useSearch, type SearchTypeFilter } from '@/hooks/use-search';
import { cn } from '@/lib/utils';

const TABS: { label: string; value: SearchTypeFilter | undefined }[] = [
  { label: 'All', value: undefined },
  { label: 'Projects', value: 'project' },
  { label: 'Docs', value: 'doc' },
  { label: 'CRs', value: 'cr' },
  { label: 'Bugs', value: 'bug' },
  { label: 'Audit Log', value: 'audit_log' },
];
const icons: Record<string, LucideIcon> = {
  project: Folder,
  document: FileText,
  change_request: GitPullRequest,
  bug: Bug,
  audit_log: Clock,
};

function EntityIcon({ type }: { type: string }) {
  const Icon = icons[type];
  return Icon ? <Icon className="h-4 w-4 shrink-0" aria-hidden /> : null;
}

export default function SearchModal() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState<SearchTypeFilter>();
  const { tenantId } = useParams();
  const navigate = useNavigate();
  const { data: results, isLoading } = useSearch(tenantId, query, activeTab);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
      event.preventDefault();
      setOpen((current) => !current);
    }
  }, []);
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  function changeOpen(nextOpen: boolean) {
    setOpen(nextOpen);
    if (!nextOpen) {
      setQuery('');
      setActiveTab(undefined);
    }
  }

  return (
    <Dialog open={open} onOpenChange={changeOpen}>
      <DialogContent className="top-[20vh] translate-y-0 overflow-hidden border-border/80 bg-card p-0 shadow-2xl sm:max-w-lg">
        <DialogTitle className="sr-only">Global search</DialogTitle>
        <DialogDescription className="sr-only">
          Search projects, change requests, bugs, documents and audit events.
        </DialogDescription>
        <div className="flex items-center border-b py-0 pl-4 pr-14">
          <Search className="h-5 w-5 text-muted-foreground" aria-hidden />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search projects, CRs, bugs, docs, audit log…"
            aria-label="Search"
            className="flex-1 border-0 bg-transparent px-4 py-4 text-sm outline-none placeholder:text-muted-foreground"
            autoFocus
          />
          <kbd className="shrink-0 rounded border bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            Esc
          </kbd>
        </div>
        <div className="flex gap-1 border-b px-3 py-2" role="tablist" aria-label="Search type">
          {TABS.map((tab) => (
            <Button
              key={tab.label}
              role="tab"
              aria-selected={activeTab === tab.value}
              variant="ghost"
              size="sm"
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                'h-7 px-2.5 text-xs',
                activeTab === tab.value && 'bg-primary/10 text-primary'
              )}
            >
              {tab.label}
            </Button>
          ))}
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {isLoading && query.length >= 2 && <LoadingState compact label="Searching" />}
          {!isLoading && results?.length === 0 && query.length >= 2 && (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No results found for “{query}”
            </div>
          )}
          {query.length < 2 && (
            <div className="py-8 text-center text-sm text-muted-foreground">
              Type at least 2 characters to search
            </div>
          )}
          {results?.map((result) => (
            <Button
              key={`${result.type}-${result.id}`}
              variant="ghost"
              onClick={() => {
                navigate(result.url);
                changeOpen(false);
              }}
              className="h-auto w-full justify-start gap-3 px-3 py-2.5 text-left"
            >
              <span className="flex items-center gap-1.5 rounded bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                <EntityIcon type={result.type} />
                <span className="capitalize">{result.type.replace('_', ' ')}</span>
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium">{result.title}</span>
                {result.snippet && (
                  <span className="block truncate text-xs text-muted-foreground">
                    {result.snippet}
                  </span>
                )}
              </span>
            </Button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
