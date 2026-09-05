import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useProject } from '../../hooks/use-projects';
import { useChangeRequests } from '../../hooks/use-change-requests';
import { useBugs } from '../../hooks/use-bugs';
import { useDocs } from '../../hooks/use-docs';
import { useWorkers, useWorkerJobs } from '../../hooks/use-workers';
import StatusBadge from '../../components/status-badge';
import SeverityBadge from '../../components/severity-badge';
import JobStatusBadge from '../../components/job-status-badge';
import JobOptionsDialog from '../../components/job-options-dialog';
import UserName from '../../components/user-name';
import { formatDateOnly } from '../../lib/format';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

export default function DashboardPage() {
  const { tenantId, projectId } = useParams();
  const navigate = useNavigate();
  const [showBuildDialog, setShowBuildDialog] = useState(false);
  const { data: project, isLoading } = useProject(tenantId, projectId);
  const { data: crsData } = useChangeRequests(tenantId, projectId, {
    page_size: 5,
  });
  const { data: bugsData } = useBugs(tenantId, projectId, { page_size: 5 });
  const { data: docs } = useDocs(tenantId, projectId);
  const { data: workers } = useWorkers(tenantId, projectId);
  const { data: jobsData } = useWorkerJobs(tenantId, projectId, { page_size: 5 });

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
  const onlineWorkers = workers?.filter((w) => w.is_online).length ?? 0;
  const totalWorkers = workers?.length ?? 0;
  const recentJobs = jobsData?.items ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{project?.name}</h1>
        {project?.description && (
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{project.description}</p>
        )}
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/crs`}
          className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-300 dark:border-slate-700 dark:bg-slate-800"
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
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {translate('projects:auto.change_requests')}
              </p>
            </div>
          </div>
        </Link>

        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/bugs`}
          className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-300 dark:border-slate-700 dark:bg-slate-800"
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
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {translate('projects:auto.bugs')}
              </p>
            </div>
          </div>
        </Link>

        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/docs`}
          className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-300 dark:border-slate-700 dark:bg-slate-800"
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
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {translate('projects:auto.documents')}
              </p>
            </div>
          </div>
        </Link>

        <Link
          to={`/tenants/${tenantId}/projects/${projectId}/workers`}
          className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition-colors hover:border-blue-300 dark:border-slate-700 dark:bg-slate-800"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 dark:bg-purple-900/30">
              <svg
                className="h-5 w-5 text-purple-600 dark:text-purple-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25z"
                />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {onlineWorkers}
                <span className="text-base font-normal text-slate-400">/{totalWorkers}</span>
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {translate('projects:auto.workers_online')}
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* Recent CRs */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">
            {translate('projects:auto.recent_change_requests')}
          </h2>
          <Link
            to={`/tenants/${tenantId}/projects/${projectId}/crs`}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            {translate('projects:auto.view_all')}
          </Link>
        </div>
        {crs.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            {translate('projects:auto.no_change_requests_yet')}
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
                  <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span className="shrink-0">{translate('projects:auto.by')}</span>
                    <UserName
                      name={cr.author?.display_name}
                      email={cr.author?.email}
                      avatarUrl={cr.author?.avatar_url}
                      fallback={translate('common:fallback.unknown')}
                      className="max-w-[14rem]"
                    />
                    <span className="shrink-0">{translate('projects:auto.middot')}</span>
                    <span className="shrink-0">{formatDateOnly(cr.created_at)}</span>
                    {typeof cr.comments_count === 'number' && cr.comments_count > 0 && (
                      <>
                        <span>{translate('projects:auto.middot')}</span>
                        <span className="inline-flex items-center gap-1">
                          <svg
                            className="h-3.5 w-3.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={1.5}
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
                            />
                          </svg>
                          {cr.comments_count}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <StatusBadge status={cr.status} />
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Recent Bugs */}
      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">
            {translate('projects:auto.recent_bugs')}
          </h2>
          <Link
            to={`/tenants/${tenantId}/projects/${projectId}/bugs`}
            className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            {translate('projects:auto.view_all')}
          </Link>
        </div>
        {bugs.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
            {translate('projects:auto.no_bugs_reported_yet')}
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
                  <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span className="shrink-0">{translate('projects:auto.by')}</span>
                    <UserName
                      name={bug.author?.display_name}
                      email={bug.author?.email}
                      avatarUrl={bug.author?.avatar_url}
                      fallback={translate('common:fallback.unknown')}
                      className="max-w-[14rem]"
                    />
                    <span>{translate('projects:auto.middot')}</span>
                    <span>{formatDateOnly(bug.created_at)}</span>
                    {typeof bug.comments_count === 'number' && bug.comments_count > 0 && (
                      <>
                        <span>{translate('projects:auto.middot')}</span>
                        <span className="inline-flex items-center gap-1">
                          <svg
                            className="h-3.5 w-3.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={1.5}
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"
                            />
                          </svg>
                          {bug.comments_count}
                        </span>
                      </>
                    )}
                  </div>
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
      {/* Recent Jobs */}
      {(recentJobs.length > 0 || totalWorkers > 0) && (
        <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
            <h2 className="font-semibold text-slate-900 dark:text-slate-100">
              {translate('projects:auto.recent_worker_jobs')}
            </h2>
            <div className="flex items-center gap-3">
              {onlineWorkers > 0 && (
                <button
                  onClick={() => setShowBuildDialog(true)}
                  className="inline-flex items-center gap-1.5 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
                >
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                    />
                  </svg>
                  {translate('projects:auto.build_on_worker')}
                </button>
              )}
              <Link
                to={`/tenants/${tenantId}/projects/${projectId}/workers`}
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                {translate('projects:auto.view_all')}
              </Link>
            </div>
          </div>
          {recentJobs.length === 0 ? (
            <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
              {translate('projects:auto.no_worker_jobs_yet')}
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-700">
              {recentJobs.map((job) => (
                <Link
                  key={job.id}
                  to={`/tenants/${tenantId}/projects/${projectId}/workers/${job.id}`}
                  className="flex items-center justify-between px-6 py-3 hover:bg-slate-50 dark:hover:bg-slate-700"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                      {job.entity_type && (
                        <span className="mr-1 text-xs text-slate-400 dark:text-slate-500">
                          {job.entity_type === 'change_request'
                            ? 'CR'
                            : job.entity_type === 'bug'
                              ? translate('projects:auto.bug_2')
                              : translate('projects:auto.doc')}
                        </span>
                      )}
                      {job.job_type === 'build' && !job.entity_title
                        ? translate('projects:auto.project_build')
                        : job.entity_title ||
                          (job.entity_id
                            ? job.entity_id.slice(0, 8)
                            : translate('projects:auto.sync'))}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {job.worker_name || translate('common:fallback.queued')}{' '}
                      {translate('projects:auto.middot')} {formatDateOnly(job.created_at)}
                    </p>
                  </div>
                  <JobStatusBadge status={job.status} />
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {showBuildDialog && (
        <JobOptionsDialog
          tenantId={requireRouteParam(tenantId, 'tenantId')}
          projectId={requireRouteParam(projectId, 'projectId')}
          jobType="build"
          onSuccess={(jobId) => {
            setShowBuildDialog(false);
            navigate(`/tenants/${tenantId}/projects/${projectId}/workers/${jobId}`);
          }}
          onCancel={() => setShowBuildDialog(false)}
        />
      )}
    </div>
  );
}
