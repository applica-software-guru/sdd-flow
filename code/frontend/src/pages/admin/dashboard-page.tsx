import { useState } from 'react';
import EmptyState from '@/components/empty-state';
import PageContainer from '@/components/page-container';
import Pagination from '@/components/pagination';
import LoadingState from '@/components/shared/loading-state';
import { translate } from '@/i18n';
import {
  type AdminOverview,
  type AdminTab,
  useAdminList,
  useAdminOverview,
} from '@/hooks/use-admin';

const tabs: Array<{ value: AdminTab; label: string }> = [
  {
    value: 'users',
    get label() {
      return translate('admin:auto.users');
    },
  },
  {
    value: 'tenants',
    get label() {
      return translate('admin:auto.tenants');
    },
  },
  {
    value: 'projects',
    get label() {
      return translate('admin:auto.projects');
    },
  },
  {
    value: 'audit-log',
    get label() {
      return translate('admin:auto.access_audit');
    },
  },
];

const columns: Record<AdminTab, Array<{ key: string; label: string }>> = {
  users: [
    {
      key: 'display_name',
      get label() {
        return translate('admin:auto.name');
      },
    },
    {
      key: 'email',
      get label() {
        return translate('admin:auto.email');
      },
    },
    {
      key: 'platform_role',
      get label() {
        return translate('admin:auto.platform_role');
      },
    },
    {
      key: 'tenant_count',
      get label() {
        return translate('admin:auto.tenants');
      },
    },
    {
      key: 'email_verified',
      get label() {
        return translate('admin:auto.verified');
      },
    },
  ],
  tenants: [
    {
      key: 'name',
      get label() {
        return translate('admin:auto.tenant');
      },
    },
    {
      key: 'slug',
      get label() {
        return translate('admin:auto.slug');
      },
    },
    {
      key: 'member_count',
      get label() {
        return translate('admin:auto.members');
      },
    },
    {
      key: 'project_count',
      get label() {
        return translate('admin:auto.projects');
      },
    },
  ],
  projects: [
    {
      key: 'name',
      get label() {
        return translate('admin:auto.project');
      },
    },
    {
      key: 'tenant_name',
      get label() {
        return translate('admin:auto.tenant');
      },
    },
    {
      key: 'slug',
      get label() {
        return translate('admin:auto.slug');
      },
    },
    {
      key: 'archived_at',
      get label() {
        return translate('admin:auto.archived');
      },
    },
  ],
  'audit-log': [
    {
      key: 'event_type',
      get label() {
        return translate('admin:auto.event');
      },
    },
    {
      key: 'summary',
      get label() {
        return translate('admin:auto.summary');
      },
    },
    {
      key: 'user_id',
      get label() {
        return translate('admin:auto.user');
      },
    },
    {
      key: 'created_at',
      get label() {
        return translate('admin:auto.date');
      },
    },
  ],
};

function display(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean')
    return value ? translate('admin:auto.yes') : translate('admin:auto.no');
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
    [translate('admin:auto.users'), props.overview?.users_count ?? 0],
    [translate('admin:auto.tenants'), props.overview?.tenants_count ?? 0],
    [translate('admin:auto.projects'), props.overview?.projects_count ?? 0],
    [translate('admin:auto.recent_logins'), props.overview?.recent_login_count ?? 0],
    [translate('admin:auto.failed_logins'), props.overview?.recent_failed_login_count ?? 0],
  ];
  return (
    <PageContainer className="space-y-6">
      <header>
        <p className="text-sm font-medium text-primary">
          {translate('admin:auto.global_platform_context')}
        </p>
        <h1 className="text-2xl font-bold">{translate('admin:auto.platform_administration')}</h1>
        <p className="text-muted-foreground">
          {translate('admin:auto.read_only_inventory_access_and_security_oversight')}
        </p>
      </header>
      <section
        aria-label={translate('admin:auto.platform_totals')}
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5"
      >
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
          aria-label={translate('admin:auto.admin_sections')}
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
            {translate('admin:auto.search_current_admin_section')}
          </label>
          <input
            id="admin-search"
            value={props.search}
            onChange={(event) => props.onSearchChange(event.target.value)}
            placeholder={
              props.activeTab === 'audit-log'
                ? translate('admin:auto.filter_by_exact_event_type')
                : translate('admin:auto.search')
            }
            className="w-full rounded-md border bg-background px-3 py-2 sm:max-w-sm"
          />
        </div>
        {props.isLoading ? (
          <LoadingState label={translate('admin:auto.loading_administration_data')} />
        ) : props.isError ? (
          <div className="p-6 text-sm text-destructive" role="alert">
            {translate('admin:auto.administration_data_could_not_be_loaded_please')}
          </div>
        ) : props.items.length === 0 ? (
          <EmptyState
            title={translate('admin:auto.no_results')}
            description={translate('admin:auto.no_platform_records_match_the_current_filters')}
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
