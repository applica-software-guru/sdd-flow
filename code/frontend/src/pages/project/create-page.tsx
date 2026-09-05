import { useState, FormEvent } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useCreateProject } from '../../hooks/use-projects';
import PageContainer from '../../components/page-container';
import { requireRouteParam } from '@/lib/route-params';
import { translate } from '@/i18n';

export default function CreatePage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const createProject = useCreateProject(requireRouteParam(tenantId, 'tenantId'));
  const navigate = useNavigate();

  const handleNameChange = (value: string) => {
    setName(value);
    if (!slug || slug === toSlug(name)) {
      setSlug(toSlug(value));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const project = await createProject.mutateAsync({ name, slug, description });
      navigate(`/tenants/${tenantId}/projects/${project.id}`);
    } catch {
      // error handled by mutation state
    }
  };

  return (
    <PageContainer>
      <div className="mb-6">
        <Link
          to={`/tenants/${tenantId}`}
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300"
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
              d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
            />
          </svg>
          {translate('projects:auto.back_to_dashboard')}
        </Link>
        <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
          {translate('projects:auto.create_a_new_project')}
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {translate('projects:auto.projects_help_you_organize_change_requests_bugs')}
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <form onSubmit={handleSubmit} className="space-y-4">
          {createProject.isError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
              {translate('projects:auto.failed_to_create_project_the_slug_may')}
            </div>
          )}

          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {translate('projects:auto.project_name')}
            </label>
            <input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              placeholder={translate('projects:auto.my_project')}
            />
          </div>

          <div>
            <label
              htmlFor="slug"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {translate('projects:auto.slug')}
            </label>
            <input
              id="slug"
              type="text"
              required
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              placeholder={translate('projects:auto.my_project_2')}
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {translate('projects:auto.url_friendly_identifier_only_lowercase_letters_numbers')}
            </p>
          </div>

          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {translate('projects:auto.description_optional')}
            </label>
            <textarea
              id="description"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              placeholder={translate('projects:auto.a_brief_description_of_the_project')}
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Link
              to={`/tenants/${tenantId}`}
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            >
              {translate('projects:auto.cancel')}
            </Link>
            <button
              type="submit"
              disabled={createProject.isPending}
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createProject.isPending ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                translate('projects:auto.create_project')
              )}
            </button>
          </div>
        </form>
      </div>
    </PageContainer>
  );
}

function toSlug(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
