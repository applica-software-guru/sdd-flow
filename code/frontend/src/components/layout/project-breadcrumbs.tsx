import { NavLink } from 'react-router-dom';
import { translate } from '@/i18n';

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
        aria-label={translate('navigation:auto.breadcrumb')}
        className="flex items-center gap-2 text-sm text-muted-foreground"
      >
        <NavLink to={`/tenants/${tenantId}`} className="font-medium hover:text-foreground">
          {translate('navigation:auto.projects')}
        </NavLink>
        <span aria-hidden="true">/</span>
        <span className="font-medium text-foreground/80">
          {projectName || translate('common:fallback.project')}
        </span>
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
          {translate('navigation:auto.project_context_is_being_synchronized_with_the')}
        </div>
      )}
    </div>
  );
}
