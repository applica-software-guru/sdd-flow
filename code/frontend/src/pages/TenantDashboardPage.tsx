import { Link, useParams, useNavigate } from 'react-router-dom';
import { useTenant, useTenants } from '../hooks/useTenants';
import { useProjects } from '../hooks/useProjects';
import EmptyState from '../components/EmptyState';

export default function TenantDashboardPage() {
  const { tenantId } = useParams();
  const navigate = useNavigate();
  const { data: tenants, isLoading: tenantsLoading } = useTenants();
  const { data: tenant } = useTenant(tenantId);
  const { data: projects, isLoading: projectsLoading } = useProjects(tenantId);

  // If no tenantId, show tenant list / picker
  if (!tenantId) {
    if (tenantsLoading) {
      return (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      );
    }

    if (!tenants || tenants.length === 0) {
      return (
        <div className="mx-auto max-w-lg">
          <EmptyState
            title="No tenants yet"
            description="Create your first tenant to get started"
            action={
              <Link
                to="/tenants/new"
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 4.5v15m7.5-7.5h-15"
                  />
                </svg>
                Create tenant
              </Link>
            }
          />
        </div>
      );
    }

    // If single tenant, redirect
    if (tenants.length === 1) {
      navigate(`/tenants/${tenants[0].id}`, { replace: true });
      return null;
    }

    return (
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-slate-900">
            Select a Tenant
          </h1>
          <Link
            to="/tenants/new"
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
            New tenant
          </Link>
        </div>

        <div className="grid gap-4">
          {tenants.map((t) => (
            <Link
              key={t.id}
              to={`/tenants/${t.id}`}
              className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-sm font-bold text-blue-700">
                {t.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">{t.name}</h3>
                <p className="text-sm text-slate-500">{t.slug}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    );
  }

  // Show projects for selected tenant
  const isLoading = projectsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {tenant?.name || 'Dashboard'}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage your projects and track progress
          </p>
        </div>
        <Link
          to={`/tenants/${tenantId}/projects/new`}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          New project
        </Link>
      </div>

      {!projects || projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create your first project to start tracking changes and bugs"
          action={
            <Link
              to={`/tenants/${tenantId}/projects/new`}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Create project
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={`/tenants/${tenantId}/projects/${project.id}`}
              className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600 group-hover:bg-blue-100">
                  <svg
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"
                    />
                  </svg>
                </div>
                {project.is_archived && (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">
                    Archived
                  </span>
                )}
              </div>
              <h3 className="mt-3 font-semibold text-slate-900">
                {project.name}
              </h3>
              <p className="mt-1 text-sm text-slate-500 line-clamp-2">
                {project.description || 'No description'}
              </p>
              <div className="mt-4 flex items-center gap-3 text-xs text-slate-400">
                <span>{project.slug}</span>
                <span>
                  Updated{' '}
                  {new Date(project.updated_at).toLocaleDateString()}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
