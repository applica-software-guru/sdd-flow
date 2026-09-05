import { Bug, FileText, Gauge, ScrollText, Settings, UsersRound, Workflow } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface NavigationProps {
  tenantId?: string;
  projectId?: string;
  projectName?: string;
  isAdmin: boolean;
  onNavigate?: () => void;
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive
      ? 'bg-primary/10 text-primary'
      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
  );
const projectLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(linkClass({ isActive }), 'border-l-2', isActive ? 'border-primary' : 'border-transparent');

export default function Navigation({
  tenantId,
  projectId,
  projectName,
  isAdmin,
  onNavigate,
}: NavigationProps) {
  if (!tenantId)
    return <p className="px-3 py-2 text-sm text-muted-foreground">Select a tenant to continue.</p>;

  const tenantItems = [
    { to: `/tenants/${tenantId}`, label: 'Dashboard', Icon: Gauge, end: true, visible: true },
    { to: `/tenants/${tenantId}/settings`, label: 'Settings', Icon: Settings, visible: isAdmin },
    {
      to: `/tenants/${tenantId}/audit-log`,
      label: 'Audit Log',
      Icon: ScrollText,
      visible: isAdmin,
    },
  ];
  const projectItems = projectId
    ? [
        {
          to: `/tenants/${tenantId}/projects/${projectId}`,
          label: 'Overview',
          Icon: Gauge,
          end: true,
        },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/crs`,
          label: 'Change Requests',
          Icon: FileText,
        },
        { to: `/tenants/${tenantId}/projects/${projectId}/bugs`, label: 'Bugs', Icon: Bug },
        { to: `/tenants/${tenantId}/projects/${projectId}/docs`, label: 'Docs', Icon: ScrollText },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/workers`,
          label: 'Workers',
          Icon: UsersRound,
        },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/settings`,
          label: 'Settings',
          Icon: Settings,
        },
      ]
    : [];

  return (
    <nav aria-label="Main navigation" className="flex flex-col gap-1">
      {tenantItems
        .filter((item) => item.visible)
        .map(({ to, label, Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={linkClass} onClick={onNavigate}>
            <Icon aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      {projectItems.length > 0 && (
        <>
          <div className="my-2 border-t" />
          <p
            className="truncate px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
            title={projectName}
          >
            Inside {projectName || 'project'}
          </p>
          {projectItems.map(({ to, label, Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={projectLinkClass} onClick={onNavigate}>
              <Icon aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </>
      )}
      {!projectId && (
        <div className="mt-2 flex items-center gap-2 px-3 text-xs text-muted-foreground">
          <Workflow aria-hidden="true" />
          Choose a project from the dashboard.
        </div>
      )}
    </nav>
  );
}
