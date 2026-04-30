import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useCreateTenant } from '../../hooks/useTenants';
import PageContainer from '../../components/PageContainer';

export default function CreatePage() {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const createTenant = useCreateTenant();
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
      const tenant = await createTenant.mutateAsync({ name, slug });
      navigate(`/tenants/${tenant.id}`);
    } catch {
      // error handled by mutation state
    }
  };

  return (
    <PageContainer>
      <div className="mb-6">
        <Link
          to="/tenants"
          className="inline-flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
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
          Back
        </Link>
        <h1 className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100">
          Create a new tenant
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          A tenant represents your organization or team
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-4">
          {createTenant.isError && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/30 p-3 text-sm text-red-700 dark:text-red-400">
              Failed to create tenant. The slug may already be taken.
            </div>
          )}

          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Tenant name
            </label>
            <input
              id="name"
              type="text"
              required
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm dark:text-slate-100 shadow-sm placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="My Organization"
            />
          </div>

          <div>
            <label
              htmlFor="slug"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Slug
            </label>
            <input
              id="slug"
              type="text"
              required
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm dark:text-slate-100 shadow-sm placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="my-organization"
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              URL-friendly identifier. Only lowercase letters, numbers, and
              hyphens.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Link
              to="/tenants"
              className="rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={createTenant.isPending}
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createTenant.isPending ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                'Create tenant'
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
