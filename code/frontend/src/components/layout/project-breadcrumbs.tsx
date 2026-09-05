import { NavLink } from 'react-router-dom';

interface ProjectBreadcrumbsProps {
  tenantId?: string;
  projectName?: string;
  section: string;
  showWarning: boolean;
}
export default function ProjectBreadcrumbs({
  tenantId,
  projectName,
  section,
  showWarning,
}: ProjectBreadcrumbsProps) {
  return (
    <div className="mx-auto mb-5 max-w-5xl space-y-3">
      <nav
        aria-label="Breadcrumb"
        className="flex items-center gap-2 text-sm text-muted-foreground"
      >
        <NavLink to={`/tenants/${tenantId}`} className="font-medium hover:text-foreground">
          Projects
        </NavLink>
        <span aria-hidden="true">/</span>
        <span className="font-medium text-foreground/80">{projectName || 'Project'}</span>
        {section && (
          <>
            <span aria-hidden="true">/</span>
            <span className="font-medium text-foreground">{section}</span>
          </>
        )}
      </nav>
      {showWarning && (
        <div
          role="status"
          className="rounded-md border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-800 dark:border-amber-700/60 dark:bg-amber-900/20 dark:text-amber-300"
        >
          Project context is being synchronized with the current route.
        </div>
      )}
    </div>
  );
}
