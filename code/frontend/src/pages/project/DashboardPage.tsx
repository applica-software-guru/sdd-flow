import { Link, useParams } from 'react-router-dom';
import { useProject } from '../../hooks/useProjects';
import { useChangeRequests } from '../../hooks/useChangeRequests';
import { useBugs } from '../../hooks/useBugs';
import { useDocs } from '../../hooks/useDocs';
import StatusBadge from '../../components/StatusBadge';
import SeverityBadge from '../../components/SeverityBadge';

export default function DashboardPage() {
  const { tenantId, projectId } = useParams();
  const { data: project, isLoading } = useProject(tenantId, projectId);
  const { data: crsData } = useChangeRequests(tenantId, projectId, {
    page_size: 5,
  });
  const { data: bugsData } = useBugs(tenantId, projectId, { page_size: 5 });
  const { data: docs } = useDocs(tenantId, projectId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  const crs = crsData?.items || [];
  const bugs = bugsData?.items || [];
  const totalCRs = crsData?.total || 0;
  const totalBugs = bugsData?.total || 0;
  const totalDocs = docs?.length || 0;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{project?.name}</h1>
        {project?.description && (
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{project.description}</p>
        )}
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/crs`}
          className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5 shadow-sm hover:border-blue-300 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 dark:bg-indigo-900/30">
              <svg
                className="h-5 w-5 text-indigo-600 dark:text-indigo-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
                />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{totalCRs}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Change Requests</p>
            </div>
          </div>
        </Link>

        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/bugs`}
          className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5 shadow-sm hover:border-blue-300 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50 dark:bg-red-900/30">
              <svg
                className="h-5 w-5 text-red-600 dark:text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 12.75c1.148 0 2.278.08 3.383.237 1.037.146 1.866.966 1.866 2.013 0 3.728-2.35 6.75-5.25 6.75S6.75 18.728 6.75 15c0-1.046.83-1.867 1.866-2.013A24.204 24.204 0 0112 12.75z"
                />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{totalBugs}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Bugs</p>
            </div>
          </div>
        </Link>

        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/docs`}
          className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5 shadow-sm hover:border-blue-300 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50 dark:bg-green-900/30">
              <svg
                className="h-5 w-5 text-green-600 dark:text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
                />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{totalDocs}</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Documents</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent CRs */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 px-6 py-4">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">
            Recent Change Requests
          </h2>
          <Link
            to={`/tenants/${tenantId}/projects/${projectId}/crs`}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700"
          >
            View all
          </Link>
        </div>
        {crs.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            No change requests yet
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {crs.map((cr) => (
              <Link
                key={cr.id}
                to={`/tenants/${tenantId}/projects/${projectId}/crs/${cr.id}`}
                className="flex items-center justify-between px-6 py-3 hover:bg-slate-50 dark:hover:bg-slate-700"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                    {cr.title}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    by on{' '}
                    {new Date(cr.created_at).toLocaleDateString()}
                  </p>
                </div>
                <StatusBadge status={cr.status} />
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Recent Bugs */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 px-6 py-4">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">Recent Bugs</h2>
          <Link
            to={`/tenants/${tenantId}/projects/${projectId}/bugs`}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700"
          >
            View all
          </Link>
        </div>
        {bugs.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            No bugs reported yet
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-700">
            {bugs.map((bug) => (
              <Link
                key={bug.id}
                to={`/tenants/${tenantId}/projects/${projectId}/bugs/${bug.id}`}
                className="flex items-center justify-between px-6 py-3 hover:bg-slate-50 dark:hover:bg-slate-700"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                    {bug.title}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    by on{' '}
                    {new Date(bug.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <SeverityBadge severity={bug.severity} />
                  <StatusBadge status={bug.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
