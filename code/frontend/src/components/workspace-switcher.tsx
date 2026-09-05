import { Fragment, useMemo, useState } from 'react';
import { Building2, Check, ChevronsUpDown, FolderKanban, Plus, Search } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useWorkspaceNavigation } from '@/hooks/use-tenants';
import { cn } from '@/lib/utils';
import type { WorkspaceNavigationTenant } from '@/types';

type VisibleTenant = WorkspaceNavigationTenant & {
  projects: WorkspaceNavigationTenant['projects'];
};

function matches(value: string | undefined, search: string) {
  return value?.toLowerCase().includes(search) ?? false;
}

function filterTenants(tenants: WorkspaceNavigationTenant[], query: string): VisibleTenant[] {
  const search = query.trim().toLowerCase();
  if (!search) return tenants;

  return tenants
    .map((tenant) => {
      const tenantMatches = matches(tenant.name, search) || matches(tenant.slug, search);
      const matchingProjects = tenant.projects.filter(
        (project) => matches(project.name, search) || matches(project.slug, search)
      );

      if (!tenantMatches && matchingProjects.length === 0) return null;
      return { ...tenant, projects: tenantMatches ? tenant.projects : matchingProjects };
    })
    .filter((tenant): tenant is VisibleTenant => tenant !== null);
}

export default function WorkspaceSwitcher() {
  const navigate = useNavigate();
  const { tenantId, projectId } = useParams();
  const { data, isError, isLoading } = useWorkspaceNavigation();
  const [query, setQuery] = useState('');

  const tenants = useMemo(() => data?.tenants ?? [], [data?.tenants]);
  const currentTenant = tenants.find((tenant) => tenant.id === tenantId);
  const currentProject = currentTenant?.projects.find((project) => project.id === projectId);
  const visibleTenants = useMemo(() => filterTenants(tenants, query), [tenants, query]);

  const triggerLabel = isLoading
    ? 'Loading workspaces…'
    : currentProject && currentTenant
      ? `${currentTenant.name} \\ ${currentProject.name}`
      : currentTenant?.name || 'Select workspace';

  const closeAndNavigate = (to: string) => {
    setQuery('');
    navigate(to);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-9 max-w-72 justify-between gap-2 bg-muted/40 px-2 hover:bg-muted"
          aria-label="Select tenant or project workspace"
        >
          {currentProject ? <FolderKanban aria-hidden="true" /> : <Building2 aria-hidden="true" />}
          <span className="min-w-0 flex-1 truncate text-left">{triggerLabel}</span>
          <ChevronsUpDown className="ml-auto opacity-50" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-80 p-2">
        <div className="relative mb-2">
          <Search
            className="pointer-events-none absolute left-2 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => event.stopPropagation()}
            className="h-9 pl-8"
            placeholder="Search tenants or projects"
            aria-label="Search tenants or projects"
          />
        </div>

        {isLoading && <p className="px-2 py-3 text-sm text-muted-foreground">Loading…</p>}
        {isError && (
          <p className="px-2 py-3 text-sm text-destructive">Unable to load workspaces.</p>
        )}
        {!isLoading && !isError && tenants.length === 0 && (
          <p className="px-2 py-3 text-sm text-muted-foreground">No workspaces available.</p>
        )}
        {!isLoading && !isError && tenants.length > 0 && visibleTenants.length === 0 && (
          <p className="px-2 py-3 text-sm text-muted-foreground">No matching workspaces.</p>
        )}

        {!isLoading && !isError && visibleTenants.length > 0 && (
          <div className="max-h-96 overflow-y-auto pr-1">
            {visibleTenants.map((tenant, index) => {
              const isCurrentTenantOverview = tenant.id === tenantId && !projectId;
              return (
                <Fragment key={tenant.id}>
                  {index > 0 && <DropdownMenuSeparator />}
                  <DropdownMenuLabel className="px-2 text-xs uppercase tracking-wide text-muted-foreground">
                    {tenant.name}
                  </DropdownMenuLabel>
                  <DropdownMenuItem
                    className={cn(
                      'cursor-pointer items-start gap-2',
                      isCurrentTenantOverview && 'bg-accent'
                    )}
                    onSelect={() => closeAndNavigate(`/tenants/${tenant.id}`)}
                  >
                    <Building2 className="mt-0.5" aria-hidden="true" />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{tenant.name}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        Tenant overview · {tenant.slug}
                      </span>
                    </span>
                    {isCurrentTenantOverview && <Check className="ml-auto" aria-hidden="true" />}
                  </DropdownMenuItem>

                  {tenant.projects.length === 0 ? (
                    <p className="px-8 py-2 text-xs text-muted-foreground">No active projects</p>
                  ) : (
                    tenant.projects.map((project) => {
                      const isCurrentProject = tenant.id === tenantId && project.id === projectId;
                      return (
                        <DropdownMenuItem
                          key={project.id}
                          className={cn(
                            'cursor-pointer items-start gap-2 pl-8',
                            isCurrentProject && 'bg-accent'
                          )}
                          onSelect={() =>
                            closeAndNavigate(`/tenants/${tenant.id}/projects/${project.id}`)
                          }
                        >
                          <FolderKanban className="mt-0.5" aria-hidden="true" />
                          <span className="min-w-0 flex-1">
                            <span className="block truncate font-medium">{project.name}</span>
                            <span className="block truncate text-xs text-muted-foreground">
                              {project.slug}
                            </span>
                          </span>
                          {project.archived_at && <Badge variant="secondary">Archived</Badge>}
                          {isCurrentProject && <Check className="ml-auto" aria-hidden="true" />}
                        </DropdownMenuItem>
                      );
                    })
                  )}
                </Fragment>
              );
            })}
          </div>
        )}

        <DropdownMenuSeparator />
        {currentTenant?.can_create_project && (
          <DropdownMenuItem
            onSelect={() => closeAndNavigate(`/tenants/${currentTenant.id}/projects/new`)}
          >
            <Plus aria-hidden="true" />
            New project
          </DropdownMenuItem>
        )}
        <DropdownMenuItem onSelect={() => closeAndNavigate('/tenants/new')}>
          <Plus aria-hidden="true" />
          New tenant
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
