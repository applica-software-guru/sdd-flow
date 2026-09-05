import {
  Activity,
  Bug,
  FileText,
  Folder,
  Gauge,
  GitPullRequest,
  History,
  MessageSquare,
  Plus,
  Search,
  Settings,
} from 'lucide-react';
import PreviewFrame from '../preview-frame';

const tenantKpis = [
  { label: 'Projects', value: '6', detail: '1 archived', icon: Folder },
  { label: 'Documentation', value: '89%', detail: '148 files · 16 pending', icon: FileText },
  { label: 'Open bugs', value: '12', detail: '2 critical · 5 major', icon: Bug, alert: true },
  { label: 'Active CRs', value: '21', detail: '8 waiting', icon: GitPullRequest },
  { label: 'Comments', value: '94', detail: '7 collaborators', icon: MessageSquare },
  { label: 'Activity', value: '240', detail: '3/5 workers online', icon: Activity },
];

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
              <p className="text-[10px] font-medium text-primary">Tenant dashboard</p>
              <h3 className="text-lg font-bold">Default</h3>
              <p className="text-xs text-muted-foreground">Overview across all projects</p>
            </div>
            <span className="inline-flex items-center gap-1 rounded bg-primary px-2 py-1 text-[10px] font-medium text-primary-foreground">
              <Plus className="h-3 w-3" /> New project
            </span>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-2 lg:grid-cols-3">
            {tenantKpis.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <div key={kpi.label} className="rounded-lg border bg-card p-3 shadow-sm">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-[10px] text-muted-foreground">{kpi.label}</p>
                      <p className="mt-1 text-lg font-bold leading-none">{kpi.value}</p>
                    </div>
                    <span
                      className={
                        kpi.alert
                          ? 'rounded bg-destructive/10 p-1 text-destructive'
                          : 'rounded bg-primary/10 p-1 text-primary'
                      }
                    >
                      <Icon className="h-3.5 w-3.5" />
                    </span>
                  </div>
                  <p className="mt-2 truncate text-[10px] text-muted-foreground">{kpi.detail}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-5 border-t-2 pt-4">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">Projects</p>
                <p className="text-[10px] text-muted-foreground">
                  Search, sort, and open a project.
                </p>
              </div>
              <div className="hidden items-center gap-2 md:flex">
                <span className="inline-flex items-center gap-1 rounded-md border bg-background px-2 py-1 text-[10px] text-muted-foreground">
                  <Search className="h-3 w-3" /> Search projects
                </span>
                <span className="rounded-md border bg-background px-2 py-1 text-[10px] text-muted-foreground">
                  Recent activity
                </span>
              </div>
            </div>
            <div className="mt-3 max-w-sm rounded-lg border bg-card p-3 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold">Hello Project</p>
                  <p className="text-[10px] text-muted-foreground">Main SDD workspace</p>
                </div>
                <Folder className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
                <PreviewMetric label="Docs" value="29/34" />
                <PreviewMetric label="Open bugs" value="4" />
                <PreviewMetric label="Active CRs" value="6" />
                <PreviewMetric label="Comments" value="18" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </PreviewFrame>
  );
}

function PreviewMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded bg-muted/70 px-2 py-1">
      <span className="text-muted-foreground">{label}</span>
      <span className="float-right font-medium">{value}</span>
    </div>
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
