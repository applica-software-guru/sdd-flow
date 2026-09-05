import { useState } from 'react';
import EmptyState from '@/components/empty-state';
import PageContainer from '@/components/page-container';
import Pagination from '@/components/pagination';
import LoadingState from '@/components/shared/loading-state';
import {
  type AdminOverview,
  type AdminTab,
  useAdminList,
  useAdminOverview,
} from '@/hooks/use-admin';

const tabs: Array<{ value: AdminTab; label: string }> = [
  { value: 'users', label: 'Users' },
  { value: 'tenants', label: 'Tenants' },
  { value: 'projects', label: 'Projects' },
  { value: 'audit-log', label: 'Access & Audit' },
];

const columns: Record<AdminTab, Array<{ key: string; label: string }>> = {
  users: [
    { key: 'display_name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'platform_role', label: 'Platform role' },
    { key: 'tenant_count', label: 'Tenants' },
    { key: 'email_verified', label: 'Verified' },
  ],
  tenants: [
    { key: 'name', label: 'Tenant' },
    { key: 'slug', label: 'Slug' },
    { key: 'member_count', label: 'Members' },
    { key: 'project_count', label: 'Projects' },
  ],
  projects: [
    { key: 'name', label: 'Project' },
    { key: 'tenant_name', label: 'Tenant' },
    { key: 'slug', label: 'Slug' },
    { key: 'archived_at', label: 'Archived' },
  ],
  'audit-log': [
    { key: 'event_type', label: 'Event' },
    { key: 'summary', label: 'Summary' },
    { key: 'user_id', label: 'User' },
    { key: 'created_at', label: 'Date' },
  ],
};

function display(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return String(value);
}

interface ViewProps {
  overview?: AdminOverview;
  activeTab: AdminTab;
  onTabChange: (tab: AdminTab) => void;
  search: string;
  onSearchChange: (value: string) => void;
  items: Array<Record<string, unknown>>;
  isLoading: boolean;
  isError?: boolean;
}

export function AdminDashboardView(props: ViewProps) {
  const cards = [
    ['Users', props.overview?.users_count ?? 0],
    ['Tenants', props.overview?.tenants_count ?? 0],
    ['Projects', props.overview?.projects_count ?? 0],
    ['Recent logins', props.overview?.recent_login_count ?? 0],
    ['Failed logins', props.overview?.recent_failed_login_count ?? 0],
  ];
  return (
    <PageContainer className="space-y-6">
      <header>
        <p className="text-sm font-medium text-primary">Global platform context</p>
        <h1 className="text-2xl font-bold">Platform administration</h1>
        <p className="text-muted-foreground">
          Read-only inventory, access, and security oversight.
        </p>
      </header>
      <section aria-label="Platform totals" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {cards.map(([label, value]) => (
          <div key={label} className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
        ))}
      </section>
      <section className="overflow-hidden rounded-lg border bg-card">
        <div
          className="flex flex-wrap gap-2 border-b p-3"
          role="tablist"
          aria-label="Admin sections"
        >
          {tabs.map((tab) => (
            <button
              key={tab.value}
              role="tab"
              aria-selected={props.activeTab === tab.value}
              onClick={() => props.onTabChange(tab.value)}
              className={`rounded-md px-3 py-2 text-sm font-medium ${props.activeTab === tab.value ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="p-3">
          <label className="sr-only" htmlFor="admin-search">
            Search current admin section
          </label>
          <input
            id="admin-search"
            value={props.search}
            onChange={(event) => props.onSearchChange(event.target.value)}
            placeholder={props.activeTab === 'audit-log' ? 'Filter by exact event type' : 'Search'}
            className="w-full rounded-md border bg-background px-3 py-2 sm:max-w-sm"
          />
        </div>
        {props.isLoading ? (
          <LoadingState label="Loading administration data" />
        ) : props.isError ? (
          <div className="p-6 text-sm text-destructive" role="alert">
            Administration data could not be loaded. Please try again.
          </div>
        ) : props.items.length === 0 ? (
          <EmptyState
            title="No results"
            description="No platform records match the current filters."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/60">
                <tr>
                  {columns[props.activeTab].map((column) => (
                    <th key={column.key} className="px-4 py-3 font-medium">
                      {column.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {props.items.map((item) => (
                  <tr key={String(item.id)} className="border-t">
                    {columns[props.activeTab].map((column) => (
                      <td key={column.key} className="px-4 py-3">
                        {display(item[column.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </PageContainer>
  );
}

export default function AdminDashboardPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>('users');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const overview = useAdminOverview();
  const list = useAdminList(activeTab, page, search);
  return (
    <>
      <AdminDashboardView
        overview={overview.data}
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          setPage(1);
          setSearch('');
        }}
        search={search}
        onSearchChange={(value) => {
          setSearch(value);
          setPage(1);
        }}
        items={list.data?.items ?? []}
        isLoading={list.isLoading}
        isError={list.isError || overview.isError}
      />
      <Pagination page={page} totalPages={list.data?.pages ?? 0} onPageChange={setPage} />
    </>
  );
}
