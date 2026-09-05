import { BookOpen, Bug, Cpu, FileText, Gauge, Settings, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import PreviewFrame from '../preview-frame';
import { PreviewNav, PreviewTopBar } from './dashboard-preview';
import { translate } from '@/i18n';

const changeRequests = () => [
  translate('landing:auto.export_accounting_data'),
  translate('landing:auto.add_project_invitations'),
  translate('landing:auto.refresh_worker_activity'),
];

export default function ProjectOverviewPreview() {
  return (
    <PreviewFrame
      label={translate('landing:auto.selected_project_overview_preview')}
      address="app.sddflow.com / projects / hello-project"
    >
      <PreviewTopBar />
      <div className="flex min-h-96">
        <aside className="hidden w-40 shrink-0 border-r bg-card p-3 sm:block">
          <PreviewNav icon={Gauge} label={translate('landing:auto.dashboard')} />
          <PreviewNav icon={Settings} label={translate('landing:auto.settings')} />
          <div className="my-3 border-t pt-3 text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
            {translate('landing:auto.inside_hello_project')}
          </div>
          <PreviewNav icon={Gauge} label={translate('landing:auto.overview')} active />
          <PreviewNav icon={FileText} label={translate('landing:auto.change_requests')} />
          <PreviewNav icon={Bug} label={translate('landing:auto.bugs')} />
          <PreviewNav icon={BookOpen} label={translate('landing:auto.docs')} />
          <PreviewNav icon={Users} label={translate('landing:auto.workers')} />
          <PreviewNav icon={Settings} label={translate('landing:auto.settings')} />
        </aside>
        <div className="min-w-0 flex-1 bg-muted/20 p-4 sm:p-6">
          <p className="text-[10px] text-muted-foreground">
            {translate('landing:auto.projects_nbsp_nbsp_hello_project_nbsp_nbsp')}{' '}
            <span className="text-foreground">{translate('landing:auto.overview')}</span>
          </p>
          <h3 className="mt-3 text-lg font-bold">{translate('landing:auto.hello_project')}</h3>
          <div className="mt-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
            <Metric icon={FileText} value="21" label={translate('landing:auto.change_requests')} />
            <Metric icon={Bug} value="1" label={translate('landing:auto.bugs')} />
            <Metric icon={BookOpen} value="22" label={translate('landing:auto.documents')} />
            <Metric icon={Cpu} value="0/0" label={translate('landing:auto.workers_online')} />
          </div>
          <div className="mt-4 overflow-hidden rounded-lg border bg-card">
            <div className="flex items-center justify-between border-b px-3 py-2 text-xs font-semibold">
              <span>{translate('landing:auto.recent_change_requests')}</span>
              <span className="text-primary">{translate('landing:auto.view_all')}</span>
            </div>
            {changeRequests().map((title) => (
              <div key={title} className="flex items-center gap-3 border-b px-3 py-2 last:border-0">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[11px] font-medium">{title}</p>
                  <p className="text-[9px] text-muted-foreground">
                    {translate('landing:auto.by_alex_morgan_sep_5_1_comment')}
                  </p>
                </div>
                <Badge variant="secondary" className="text-[9px]">
                  {translate('landing:auto.draft')}
                </Badge>
              </div>
            ))}
          </div>
          <div className="mt-3 overflow-hidden rounded-lg border bg-card">
            <div className="flex items-center justify-between border-b px-3 py-2 text-xs font-semibold">
              <span>{translate('landing:auto.recent_bugs')}</span>
              <span className="text-primary">{translate('landing:auto.view_all')}</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-[11px] font-medium">
                  {translate('landing:auto.cli_sync_does_not_preserve_folder_order')}
                </p>
                <p className="text-[9px] text-muted-foreground">
                  {translate('landing:auto.by_jamie_chen_sep_4_1_comment')}
                </p>
              </div>
              <Badge className="bg-amber-500/15 text-[9px] text-amber-700 hover:bg-amber-500/15 dark:text-amber-400">
                {translate('landing:auto.minor')}
              </Badge>
              <Badge variant="secondary" className="text-[9px]">
                {translate('landing:auto.open')}
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
