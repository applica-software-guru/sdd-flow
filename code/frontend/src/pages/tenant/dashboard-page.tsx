import { useMemo, useState } from 'react';
import {
  Activity,
  ArrowUpDown,
  Bug,
  FileText,
  FolderKanban,
  GitPullRequest,
  MessageSquare,
  Plus,
  Search,
} from 'lucide-react';
import { Link, Navigate, useParams } from 'react-router-dom';
import EmptyState from '@/components/empty-state';
import PageContainer from '@/components/page-container';
import LoadingState from '@/components/shared/loading-state';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTenantDashboard, useTenants } from '@/hooks/use-tenants';
import { formatDateOnly, formatNumber } from '@/lib/format';
import type { TenantDashboardKpis, TenantDashboardProject } from '@/types';
import { translate } from '@/i18n';

const sortLabels = {
  get activity() {
    return translate('tenants:auto.recent_activity');
  },
  get bugs() {
    return translate('tenants:auto.open_bugs');
  },
  get crs() {
    return translate('tenants:auto.active_crs');
  },
  get docs() {
    return translate('tenants:auto.docs_sync');
  },
  get name() {
    return translate('tenants:auto.name');
  },
} as const;

type SortKey = keyof typeof sortLabels;

function syncPercentage(project: TenantDashboardProject): number {
  const { documents_synced: synced, documents_total: total } = project.stats;
  return total > 0 ? Math.round((synced / total) * 100) : 0;
}

function sortProjects(projects: TenantDashboardProject[], sort: SortKey): TenantDashboardProject[] {
  return [...projects].sort((a, b) => {
    if (sort === 'name') return a.name.localeCompare(b.name);
    if (sort === 'bugs') return b.stats.open_bugs - a.stats.open_bugs;
    if (sort === 'crs') return b.stats.active_crs - a.stats.active_crs;
    if (sort === 'docs') return syncPercentage(a) - syncPercentage(b);

    const aTime = a.stats.last_activity_at ? new Date(a.stats.last_activity_at).getTime() : 0;
    const bTime = b.stats.last_activity_at ? new Date(b.stats.last_activity_at).getTime() : 0;
    return bTime - aTime;
  });
}

function TenantPicker() {
  const { data: tenants, isLoading } = useTenants();

  if (isLoading) return <LoadingState label={translate('tenants:auto.loading_tenants')} />;

  if (!tenants || tenants.length === 0) {
    return (
      <PageContainer>
        <EmptyState
          title={translate('tenants:auto.no_tenants_yet')}
          description={translate('tenants:auto.create_your_first_tenant_to_get_started')}
          action={
            <Button asChild>
              <Link to="/tenants/new">
                <Plus />
                {translate('tenants:auto.create_tenant')}
              </Link>
            </Button>
          }
        />
      </PageContainer>
    );
  }

  if (tenants.length === 1) return <Navigate to={`/tenants/${tenants[0].id}`} replace />;

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-foreground">
          {translate('tenants:auto.select_a_tenant')}
        </h1>
        <Button asChild>
          <Link to="/tenants/new">
            <Plus />
            {translate('tenants:auto.new_tenant')}
          </Link>
        </Button>
      </div>

      <div className="grid gap-4">
        {tenants.map((tenant) => (
          <Link
            key={tenant.id}
            to={`/tenants/${tenant.id}`}
            className="flex items-center gap-4 rounded-lg border bg-card p-4 text-card-foreground shadow-sm transition-all hover:border-primary/50 hover:shadow-md"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-sm font-bold text-primary">
              {tenant.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="font-semibold">{tenant.name}</h3>
              <p className="text-sm text-muted-foreground">{tenant.slug}</p>
            </div>
          </Link>
        ))}
      </div>
    </PageContainer>
  );
}

function KpiGrid({ kpis }: { kpis: TenantDashboardKpis }) {
  const cards = [
    {
      get title() {
        return translate('tenants:auto.projects');
      },
      value: formatNumber(kpis.active_projects),
      description:
        kpis.archived_projects > 0
          ? `${kpis.archived_projects} archived`
          : translate('tenants:auto.active_portfolio'),
      icon: FolderKanban,
    },
    {
      get title() {
        return translate('tenants:auto.documentation');
      },
      value: `${kpis.docs_sync_percentage}%`,
      description: `${formatNumber(kpis.documents_total)} files · ${formatNumber(
        kpis.documents_pending
      )} pending`,
      icon: FileText,
    },
    {
      get title() {
        return translate('tenants:auto.open_bugs');
      },
      value: formatNumber(kpis.open_bugs),
      description: `${kpis.critical_bugs} critical · ${kpis.major_bugs} major`,
      icon: Bug,
      warning: kpis.critical_bugs > 0,
    },
    {
      get title() {
        return translate('tenants:auto.active_crs');
      },
      value: formatNumber(kpis.active_crs),
      description: `${formatNumber(kpis.review_queue_crs)} waiting for review/apply`,
      icon: GitPullRequest,
    },
    {
      get title() {
        return translate('tenants:auto.comments');
      },
      value: formatNumber(kpis.comments_in_window),
      description: `${formatNumber(kpis.distinct_commenters_in_window)} collaborators in 30 days`,
      icon: MessageSquare,
    },
    {
      get title() {
        return translate('tenants:auto.activity');
      },
      value: formatNumber(kpis.activity_events_in_window),
      description: `${kpis.workers_online}/${kpis.workers_total} workers online`,
      icon: Activity,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title}>
            <CardContent className="flex items-start justify-between gap-4 p-5">
              <div>
                <p className="text-sm font-medium text-muted-foreground">{card.title}</p>
                <p className="mt-2 text-3xl font-bold tracking-tight text-foreground">
                  {card.value}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">{card.description}</p>
              </div>
              <div
                className={
                  card.warning
                    ? translate('tenants:auto.rounded_lg_bg_destructive_10_p_2')
                    : translate('tenants:auto.rounded_lg_bg_primary_10_p_2')
                }
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function ProjectPortfolio({
  tenantId,
  projects,
}: {
  tenantId: string;
  projects: TenantDashboardProject[];
}) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortKey>('activity');
  const visibleProjects = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = query
      ? projects.filter(
          (project) =>
            project.name.toLowerCase().includes(query) || project.slug.toLowerCase().includes(query)
        )
      : projects;
    return sortProjects(filtered, sort);
  }, [projects, search, sort]);

  return (
    <section className="space-y-4" aria-labelledby="tenant-projects-heading">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h2 id="tenant-projects-heading" className="text-lg font-semibold text-foreground">
            {translate('tenants:auto.projects')}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {translate('tenants:auto.search_sort_and_open_a_project_from')}
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:flex-row md:w-auto">
          <div className="relative sm:w-64">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={translate('tenants:auto.search_projects')}
              className="pl-9"
              aria-label={translate('tenants:auto.search_projects')}
            />
          </div>
          <Select value={sort} onValueChange={(value) => setSort(value as SortKey)}>
            <SelectTrigger className="sm:w-44" aria-label={translate('tenants:auto.sort_projects')}>
              <ArrowUpDown className="mr-2 h-4 w-4" aria-hidden="true" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(sortLabels).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {visibleProjects.length === 0 ? (
        <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
          {translate('tenants:auto.no_projects_match_your_search')}
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {visibleProjects.map((project) => (
            <Link
              key={project.id}
              to={`/tenants/${tenantId}/projects/${project.id}`}
              className="group rounded-lg border bg-card p-4 text-card-foreground transition-all hover:border-primary/50 hover:shadow-sm"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-foreground group-hover:text-primary">
                      {project.name}
                    </h3>
                    {project.archived_at && (
                      <Badge variant="secondary">{translate('tenants:auto.archived')}</Badge>
                    )}
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {project.description || translate('common:fallback.noDescription')}
                  </p>
                </div>
                <FolderKanban
                  className="h-5 w-5 shrink-0 text-muted-foreground"
                  aria-hidden="true"
                />
              </div>
              <div className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
                <Metric
                  label={translate('tenants:auto.docs')}
                  value={`${project.stats.documents_synced}/${project.stats.documents_total}`}
                />
                <Metric
                  label={translate('tenants:auto.pending_docs')}
                  value={project.stats.documents_pending}
                />
                <Metric
                  label={translate('tenants:auto.open_bugs')}
                  value={project.stats.open_bugs}
                />
                <Metric
                  label={translate('tenants:auto.active_crs')}
                  value={project.stats.active_crs}
                />
                <Metric
                  label={translate('tenants:auto.comments')}
                  value={project.stats.comments_in_window}
                />
                <Metric
                  label={translate('tenants:auto.workers')}
                  value={`${project.stats.workers_online}/${project.stats.workers_total}`}
                />
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                {project.stats.last_activity_at
                  ? `Last activity ${formatDateOnly(project.stats.last_activity_at)}`
                  : project.slug}
              </p>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md bg-muted/60 px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="float-right font-medium text-foreground">{value}</span>
    </div>
  );
}

export default function DashboardPage() {
  const { tenantId } = useParams();
  const { data: tenants } = useTenants();
  const { data: dashboard, isLoading, isError, refetch } = useTenantDashboard(tenantId);
  const currentTenant = tenants?.find((tenant) => tenant.id === tenantId);
  const canManageTenant = currentTenant?.role === 'owner' || currentTenant?.role === 'admin';

  if (!tenantId) return <TenantPicker />;

  if (isLoading) return <LoadingState label={translate('tenants:auto.loading_tenant_dashboard')} />;

  if (isError || !dashboard) {
    return (
      <PageContainer>
        <EmptyState
          title={translate('tenants:auto.dashboard_unavailable')}
          description={translate('tenants:auto.we_could_not_load_tenant_kpis_right')}
          action={<Button onClick={() => void refetch()}>{translate('tenants:auto.retry')}</Button>}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <p className="text-sm font-medium text-primary">
            {translate('tenants:auto.tenant_dashboard')}
          </p>
          <h1 className="mt-1 text-2xl font-bold text-foreground">{dashboard.tenant.name}</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            {translate('tenants:auto.overview_across_all_projects_choose_a_project')}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {canManageTenant && (
            <Button asChild variant="outline">
              <Link to={`/tenants/${tenantId}/settings`}>
                {translate('tenants:auto.tenant_settings')}
              </Link>
            </Button>
          )}
          <Button asChild>
            <Link to={`/tenants/${tenantId}/projects/new`}>
              <Plus />
              {translate('tenants:auto.new_project')}
            </Link>
          </Button>
        </div>
      </div>

      {dashboard.projects.length === 0 ? (
        <EmptyState
          title={translate('tenants:auto.no_projects_yet')}
          description={translate('tenants:auto.create_your_first_project_to_start_producing')}
          action={
            <Button asChild>
              <Link to={`/tenants/${tenantId}/projects/new`}>
                {translate('tenants:auto.create_project')}
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-6">
          <KpiGrid kpis={dashboard.kpis} />
          <div className="border-t-2 border-border pt-6">
            <ProjectPortfolio tenantId={tenantId} projects={dashboard.projects} />
          </div>
        </div>
      )}
    </PageContainer>
  );
}
