import {
  Bug,
  FileText,
  Gauge,
  ScrollText,
  Settings,
  Shield,
  UsersRound,
  Workflow,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';

interface NavigationProps {
  tenantId?: string;
  projectId?: string;
  projectName?: string;
  isAdmin: boolean;
  isSuperUser: boolean;
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
  isSuperUser,
  onNavigate,
}: NavigationProps) {
  const { t } = useTranslation('navigation');
  const adminLink = isSuperUser ? (
    <NavLink to="/admin" className={linkClass} onClick={onNavigate}>
      <Shield aria-hidden="true" />
      {t('platformAdmin')}
    </NavLink>
  ) : null;
  if (!tenantId)
    return (
      <nav aria-label={t('main')} className="flex flex-col gap-1">
        {adminLink}
        <p className="px-3 py-2 text-sm text-muted-foreground">{t('selectTenant')}</p>
      </nav>
    );

  const tenantItems = [
    { to: `/tenants/${tenantId}`, label: t('dashboard'), Icon: Gauge, end: true, visible: true },
    { to: `/tenants/${tenantId}/settings`, label: t('settings'), Icon: Settings, visible: isAdmin },
    {
      to: `/tenants/${tenantId}/audit-log`,
      label: t('auditLog'),
      Icon: ScrollText,
      visible: isAdmin,
    },
  ];
  const projectItems = projectId
    ? [
        {
          to: `/tenants/${tenantId}/projects/${projectId}`,
          label: t('overview'),
          Icon: Gauge,
          end: true,
        },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/crs`,
          label: t('changeRequests'),
          Icon: FileText,
        },
        { to: `/tenants/${tenantId}/projects/${projectId}/bugs`, label: t('bugs'), Icon: Bug },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/docs`,
          label: t('docs'),
          Icon: ScrollText,
        },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/workers`,
          label: t('workers'),
          Icon: UsersRound,
        },
        {
          to: `/tenants/${tenantId}/projects/${projectId}/settings`,
          label: t('settings'),
          Icon: Settings,
        },
      ]
    : [];

  return (
    <nav aria-label={t('main')} className="flex flex-col gap-1">
      {adminLink}
      {adminLink && <div className="my-2 border-t" />}
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
            {t('insideProject', { project: projectName || t('projectFallback') })}
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
          {t('chooseProject')}
        </div>
      )}
    </nav>
  );
}
