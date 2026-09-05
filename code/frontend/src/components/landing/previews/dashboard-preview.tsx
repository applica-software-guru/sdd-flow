import { Folder, Gauge, History, Plus, Search, Settings } from 'lucide-react';
import PreviewFrame from '../preview-frame';

export default function DashboardPreview() {
  return (
    <PreviewFrame label="Tenant project dashboard preview">
      <PreviewTopBar />
      <div className="flex min-h-80">
        <aside className="hidden w-40 shrink-0 border-r bg-card p-3 sm:block">
          <PreviewNav icon={Gauge} label="Dashboard" active />
          <PreviewNav icon={Settings} label="Settings" />
          <PreviewNav icon={History} label="Audit Log" />
          <div className="mt-3 border-t pt-3 text-[10px] leading-4 text-muted-foreground">
            Choose a project from the dashboard.
          </div>
        </aside>
        <div className="min-w-0 flex-1 bg-muted/20 p-4 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-bold">Default</h3>
              <p className="text-xs text-muted-foreground">
                Manage your projects and track progress
              </p>
            </div>
            <span className="inline-flex items-center gap-1 rounded bg-primary px-2 py-1 text-[10px] font-medium text-primary-foreground">
              <Plus className="h-3 w-3" /> New project
            </span>
          </div>
          <div className="mt-6 max-w-64 rounded-lg border bg-card p-4 shadow-sm">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Folder className="h-5 w-5" />
            </span>
            <p className="mt-4 text-sm font-semibold">Hello Project</p>
            <p className="mt-1 text-xs text-muted-foreground">No description</p>
            <div className="mt-5 flex gap-3 text-[10px] text-muted-foreground">
              <span>hello-project</span>
              <span>Updated Sep 5</span>
            </div>
          </div>
        </div>
      </div>
    </PreviewFrame>
  );
}

export function PreviewTopBar() {
  return (
    <div className="flex h-10 items-center border-b px-3 text-xs">
      <span className="flex h-6 w-6 items-center justify-center rounded bg-primary font-bold text-primary-foreground">
        S
      </span>
      <span className="ml-2 font-semibold">SDD Flow</span>
      <span className="ml-4 rounded border bg-background px-2 py-1 text-muted-foreground">
        Default
      </span>
      <Search className="ml-auto h-4 w-4 text-muted-foreground" />
    </div>
  );
}

export function PreviewNav({
  icon: Icon,
  label,
  active,
}: {
  icon: typeof Gauge;
  label: string;
  active?: boolean;
}) {
  return (
    <div
      className={`mb-1 flex items-center gap-2 rounded px-2 py-1.5 text-[10px] ${active ? 'bg-primary/10 font-medium text-primary' : 'text-muted-foreground'}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </div>
  );
}
