import { Suspense, useMemo, useState } from 'react';
import { Outlet, useLocation, useParams } from 'react-router-dom';
import AppTopBar from '@/components/layout/app-top-bar';
import MobileNavigation from '@/components/layout/mobile-navigation';
import ProjectBreadcrumbs from '@/components/layout/project-breadcrumbs';
import Sidebar from '@/components/layout/sidebar';
import SearchModal from '@/components/search-modal';
import LoadingState from '@/components/shared/loading-state';
import { useCurrentUser } from '@/hooks/use-auth';
import { useLastTenantId } from '@/hooks/use-last-tenant-id';
import { useProject, useProjects } from '@/hooks/use-projects';
import { useTenantMembers } from '@/hooks/use-tenants';

function sectionFromPath(pathname: string, projectId?: string): string {
  if (!projectId) return '';
  const trailing = pathname.split(`/projects/${projectId}`)[1] ?? '';
  if (!trailing || trailing === '/') return 'Overview';
  if (trailing.startsWith('/crs')) return 'Change Requests';
  if (trailing.startsWith('/bugs')) return 'Bugs';
  if (trailing.startsWith('/docs')) return 'Docs';
  if (trailing.startsWith('/workers')) return 'Workers';
  if (trailing.startsWith('/settings')) return 'Settings';
  return 'Overview';
}

export default function Layout() {
  const { tenantId, projectId } = useParams();
  const location = useLocation();
  const sidebarTenantId = useLastTenantId(tenantId);
  const { data: user } = useCurrentUser();
  const { data: project, isLoading, isError } = useProject(tenantId, projectId);
  const { data: projects } = useProjects(tenantId);
  const { data: members } = useTenantMembers(sidebarTenantId);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isAdmin = useMemo(() => {
    const role = members?.find((member) => member.user_id === user?.id)?.role;
    return role === 'owner' || role === 'admin';
  }, [members, user?.id]);
  const activeProject =
    project?.id === projectId ? project : projects?.find((item) => item.id === projectId);
  const projectSection = sectionFromPath(location.pathname, projectId);
  const showWarning = Boolean(tenantId && projectId && !activeProject && !isLoading && isError);
  const navigationProps = {
    tenantId: sidebarTenantId,
    projectId,
    projectName: activeProject?.name,
    isAdmin,
    isSuperUser: user?.platform_role === 'super_user',
  };

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <SearchModal />
      <MobileNavigation {...navigationProps} open={mobileOpen} onOpenChange={setMobileOpen} />
      <AppTopBar user={user} onOpenNavigation={() => setMobileOpen(true)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar {...navigationProps} />
        <main className="flex-1 overflow-y-auto bg-muted/40 p-4 sm:p-6">
          {tenantId && projectId && (
            <ProjectBreadcrumbs
              tenantId={sidebarTenantId}
              projectName={activeProject?.name}
              section={projectSection}
              showWarning={showWarning}
            />
          )}
          <Suspense fallback={<LoadingState label="Loading page" className="min-h-64" />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
