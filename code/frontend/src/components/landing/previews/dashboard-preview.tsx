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
import { translate } from '@/i18n';

const tenantKpis = [
  {
    get label() {
      return translate('landing:auto.projects');
    },
    value: '6',
    get detail() {
      return translate('landing:auto.1_archived');
    },
    icon: Folder,
  },
  {
    get label() {
      return translate('landing:auto.documentation');
    },
    value: '89%',
    get detail() {
      return translate('landing:auto.148_files_16_pending');
    },
    icon: FileText,
  },
  {
    get label() {
      return translate('landing:auto.open_bugs');
    },
    value: '12',
    get detail() {
      return translate('landing:auto.2_critical_5_major');
    },
    icon: Bug,
    alert: true,
  },
  {
    get label() {
      return translate('landing:auto.active_crs');
    },
    value: '21',
    get detail() {
      return translate('landing:auto.8_waiting');
    },
    icon: GitPullRequest,
  },
  {
    get label() {
      return translate('landing:auto.comments');
    },
    value: '94',
    get detail() {
      return translate('landing:auto.7_collaborators');
    },
    icon: MessageSquare,
  },
  {
    get label() {
      return translate('landing:auto.activity');
    },
    value: '240',
    get detail() {
      return translate('landing:auto.3_5_workers_online');
    },
    icon: Activity,
  },
];

export default function DashboardPreview() {
  return (
    <PreviewFrame label={translate('landing:auto.tenant_project_dashboard_preview')}>
      <PreviewTopBar />
      <div className="flex min-h-80">
        <aside className="hidden w-40 shrink-0 border-r bg-card p-3 sm:block">
          <PreviewNav icon={Gauge} label={translate('landing:auto.dashboard')} active />
          <PreviewNav icon={Settings} label={translate('landing:auto.settings')} />
          <PreviewNav icon={History} label={translate('landing:auto.audit_log')} />
          <div className="mt-3 border-t pt-3 text-[10px] leading-4 text-muted-foreground">
            {translate('landing:auto.choose_a_project_from_the_dashboard')}
          </div>
        </aside>
        <div className="min-w-0 flex-1 bg-muted/20 p-4 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[10px] font-medium text-primary">
                {translate('landing:auto.tenant_dashboard')}
              </p>
              <h3 className="text-lg font-bold">{translate('landing:auto.default')}</h3>
              <p className="text-xs text-muted-foreground">
                {translate('landing:auto.overview_across_all_projects')}
              </p>
            </div>
            <span className="inline-flex items-center gap-1 rounded bg-primary px-2 py-1 text-[10px] font-medium text-primary-foreground">
              <Plus className="h-3 w-3" /> {translate('landing:auto.new_project')}
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
                          ? translate('landing:auto.rounded_bg_destructive_10_p_1_text')
                          : translate('landing:auto.rounded_bg_primary_10_p_1_text')
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
                <p className="text-sm font-semibold">{translate('landing:auto.projects')}</p>
                <p className="text-[10px] text-muted-foreground">
                  {translate('landing:auto.search_sort_and_open_a_project')}
                </p>
              </div>
              <div className="hidden items-center gap-2 md:flex">
                <span className="inline-flex items-center gap-1 rounded-md border bg-background px-2 py-1 text-[10px] text-muted-foreground">
                  <Search className="h-3 w-3" /> {translate('landing:auto.search_projects')}
                </span>
                <span className="rounded-md border bg-background px-2 py-1 text-[10px] text-muted-foreground">
                  {translate('landing:auto.recent_activity')}
                </span>
              </div>
            </div>
            <div className="mt-3 max-w-sm rounded-lg border bg-card p-3 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold">{translate('landing:auto.hello_project')}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {translate('landing:auto.main_sdd_workspace')}
                  </p>
                </div>
                <Folder className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
                <PreviewMetric label={translate('landing:auto.docs')} value="29/34" />
                <PreviewMetric label={translate('landing:auto.open_bugs')} value="4" />
                <PreviewMetric label={translate('landing:auto.active_crs')} value="6" />
                <PreviewMetric label={translate('landing:auto.comments')} value="18" />
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
        {translate('landing:auto.default')}
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
