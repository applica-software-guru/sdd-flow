import { BookOpen, Bug, Cpu, FileText, Gauge, Settings, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import PreviewFrame from '../preview-frame';
import { PreviewNav, PreviewTopBar } from './dashboard-preview';

const changeRequests = [
  'Export accounting data',
  'Add project invitations',
  'Refresh worker activity',
];

export default function ProjectOverviewPreview() {
  return (
    <PreviewFrame
      label="Selected project overview preview"
      address="app.sddflow.com / projects / hello-project"
    >
      <PreviewTopBar />
      <div className="flex min-h-96">
        <aside className="hidden w-40 shrink-0 border-r bg-card p-3 sm:block">
          <PreviewNav icon={Gauge} label="Dashboard" />
          <PreviewNav icon={Settings} label="Settings" />
          <div className="my-3 border-t pt-3 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
            Inside Hello Project
          </div>
          <PreviewNav icon={Gauge} label="Overview" active />
          <PreviewNav icon={FileText} label="Change Requests" />
          <PreviewNav icon={Bug} label="Bugs" />
          <PreviewNav icon={BookOpen} label="Docs" />
          <PreviewNav icon={Users} label="Workers" />
          <PreviewNav icon={Settings} label="Settings" />
        </aside>
        <div className="min-w-0 flex-1 bg-muted/20 p-4 sm:p-6">
          <p className="text-[10px] text-muted-foreground">
            Projects &nbsp;/&nbsp; Hello Project &nbsp;/&nbsp;{' '}
            <span className="text-foreground">Overview</span>
          </p>
          <h3 className="mt-3 text-lg font-bold">Hello Project</h3>
          <div className="mt-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
            <Metric icon={FileText} value="21" label="Change Requests" />
            <Metric icon={Bug} value="1" label="Bugs" />
            <Metric icon={BookOpen} value="22" label="Documents" />
            <Metric icon={Cpu} value="0/0" label="Workers Online" />
          </div>
          <div className="mt-4 overflow-hidden rounded-lg border bg-card">
            <div className="flex items-center justify-between border-b px-3 py-2 text-xs font-semibold">
              <span>Recent Change Requests</span>
              <span className="text-primary">View all</span>
            </div>
            {changeRequests.map((title) => (
              <div key={title} className="flex items-center gap-3 border-b px-3 py-2 last:border-0">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[11px] font-medium">{title}</p>
                  <p className="text-[9px] text-muted-foreground">
                    by Alex Morgan · Sep 5 · 1 comment
                  </p>
                </div>
                <Badge variant="secondary" className="text-[9px]">
                  Draft
                </Badge>
              </div>
            ))}
          </div>
          <div className="mt-3 overflow-hidden rounded-lg border bg-card">
            <div className="flex items-center justify-between border-b px-3 py-2 text-xs font-semibold">
              <span>Recent Bugs</span>
              <span className="text-primary">View all</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-[11px] font-medium">
                  CLI sync does not preserve folder order
                </p>
                <p className="text-[9px] text-muted-foreground">
                  by Jamie Chen · Sep 4 · 1 comment
                </p>
              </div>
              <Badge className="bg-amber-500/15 text-[9px] text-amber-700 hover:bg-amber-500/15 dark:text-amber-400">
                Minor
              </Badge>
              <Badge variant="secondary" className="text-[9px]">
                Open
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </PreviewFrame>
  );
}

function Metric({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof FileText;
  value: string;
  label: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <div className="flex items-start gap-2">
        <span className="rounded-md bg-primary/10 p-1.5 text-primary">
          <Icon className="h-4 w-4" />
        </span>
        <div>
          <p className="text-base font-bold">{value}</p>
          <p className="text-[9px] text-muted-foreground">{label}</p>
        </div>
      </div>
    </div>
  );
}
