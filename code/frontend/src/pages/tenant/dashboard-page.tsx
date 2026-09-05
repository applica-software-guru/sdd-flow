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
import { formatDateOnly } from '@/lib/format';
import type { TenantDashboardKpis, TenantDashboardProject } from '@/types';

const sortLabels = {
  activity: 'Recent activity',
  bugs: 'Open bugs',
  crs: 'Active CRs',
  docs: 'Docs sync',
  name: 'Name',
} as const;

type SortKey = keyof typeof sortLabels;

function formatNumber(value: number): string {
  return new Intl.NumberFormat().format(value);
}

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

  if (isLoading) return <LoadingState label="Loading tenants" />;

  if (!tenants || tenants.length === 0) {
    return (
      <PageContainer>
        <EmptyState
          title="No tenants yet"
          description="Create your first tenant to get started"
          action={
            <Button asChild>
              <Link to="/tenants/new">
                <Plus />
                Create tenant
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
        <h1 className="text-2xl font-bold text-foreground">Select a Tenant</h1>
        <Button asChild>
          <Link to="/tenants/new">
            <Plus />
            New tenant
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
      title: 'Projects',
      value: formatNumber(kpis.active_projects),
      description:
        kpis.archived_projects > 0 ? `${kpis.archived_projects} archived` : 'Active portfolio',
      icon: FolderKanban,
    },
    {
      title: 'Documentation',
      value: `${kpis.docs_sync_percentage}%`,
      description: `${formatNumber(kpis.documents_total)} files · ${formatNumber(
        kpis.documents_pending
      )} pending`,
      icon: FileText,
    },
    {
      title: 'Open bugs',
      value: formatNumber(kpis.open_bugs),
      description: `${kpis.critical_bugs} critical · ${kpis.major_bugs} major`,
      icon: Bug,
      warning: kpis.critical_bugs > 0,
    },
    {
      title: 'Active CRs',
      value: formatNumber(kpis.active_crs),
      description: `${formatNumber(kpis.review_queue_crs)} waiting for review/apply`,
      icon: GitPullRequest,
    },
    {
      title: 'Comments',
      value: formatNumber(kpis.comments_in_window),
      description: `${formatNumber(kpis.distinct_commenters_in_window)} collaborators in 30 days`,
      icon: MessageSquare,
    },
    {
      title: 'Activity',
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
                    ? 'rounded-lg bg-destructive/10 p-2 text-destructive'
                    : 'rounded-lg bg-primary/10 p-2 text-primary'
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
            Projects
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Search, sort, and open a project from this tenant.
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
              placeholder="Search projects"
              className="pl-9"
              aria-label="Search projects"
            />
          </div>
          <Select value={sort} onValueChange={(value) => setSort(value as SortKey)}>
            <SelectTrigger className="sm:w-44" aria-label="Sort projects">
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
          No projects match your search.
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
                    {project.archived_at && <Badge variant="secondary">Archived</Badge>}
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                    {project.description || 'No description'}
                  </p>
                </div>
                <FolderKanban
                  className="h-5 w-5 shrink-0 text-muted-foreground"
                  aria-hidden="true"
                />
              </div>
              <div className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
                <Metric
                  label="Docs"
                  value={`${project.stats.documents_synced}/${project.stats.documents_total}`}
                />
                <Metric label="Pending docs" value={project.stats.documents_pending} />
                <Metric label="Open bugs" value={project.stats.open_bugs} />
                <Metric label="Active CRs" value={project.stats.active_crs} />
                <Metric label="Comments" value={project.stats.comments_in_window} />
                <Metric
                  label="Workers"
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

  if (isLoading) return <LoadingState label="Loading tenant dashboard" />;

  if (isError || !dashboard) {
    return (
      <PageContainer>
        <EmptyState
          title="Dashboard unavailable"
          description="We could not load tenant KPIs right now. Please try again."
          action={<Button onClick={() => void refetch()}>Retry</Button>}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div>
          <p className="text-sm font-medium text-primary">Tenant dashboard</p>
          <h1 className="mt-1 text-2xl font-bold text-foreground">{dashboard.tenant.name}</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Overview across all projects. Choose a project to work on docs, CRs, bugs, workers, and
            project settings.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {canManageTenant && (
            <Button asChild variant="outline">
              <Link to={`/tenants/${tenantId}/settings`}>Tenant settings</Link>
            </Button>
          )}
          <Button asChild>
            <Link to={`/tenants/${tenantId}/projects/new`}>
              <Plus />
              New project
            </Link>
          </Button>
        </div>
      </div>

      {dashboard.projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create your first project to start producing SDD documentation, CRs, and bug reports."
          action={
            <Button asChild>
              <Link to={`/tenants/${tenantId}/projects/new`}>Create project</Link>
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
