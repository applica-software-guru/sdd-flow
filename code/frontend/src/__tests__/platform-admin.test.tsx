import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import Navigation from '../components/layout/navigation';
import { AdminDashboardView } from '../pages/admin/dashboard-page';

describe('platform administration', () => {
  it('shows global admin navigation only to super users', () => {
    const superMarkup = renderToStaticMarkup(
      <MemoryRouter>
        <Navigation isAdmin={false} isSuperUser />
      </MemoryRouter>
    );
    const userMarkup = renderToStaticMarkup(
      <MemoryRouter>
        <Navigation isAdmin={false} isSuperUser={false} />
      </MemoryRouter>
    );

    expect(superMarkup).toContain('Platform Admin');
    expect(superMarkup).toContain('href="/admin"');
    expect(userMarkup).not.toContain('Platform Admin');
  });

  it('renders global totals and safe inventory tabs', () => {
    const markup = renderToStaticMarkup(
      <AdminDashboardView
        overview={{
          users_count: 12,
          tenants_count: 4,
          projects_count: 9,
          recent_login_count: 7,
          recent_failed_login_count: 1,
          recent_events: [],
        }}
        activeTab="users"
        onTabChange={() => undefined}
        search=""
        onSearchChange={() => undefined}
        items={[
          {
            id: 'u1',
            email: 'operator@example.com',
            display_name: 'Operator',
            platform_role: 'super_user',
            email_verified: true,
            tenant_count: 2,
          },
        ]}
        isLoading={false}
      />
    );

    expect(markup).toContain('Platform administration');
    expect(markup).toContain('12');
    expect(markup).toContain('Users');
    expect(markup).toContain('Tenants');
    expect(markup).toContain('Projects');
    expect(markup).toContain('Access &amp; Audit');
    expect(markup).toContain('operator@example.com');
    expect(markup).not.toContain('password_hash');
  });

  it('renders an explicit error state', () => {
    const markup = renderToStaticMarkup(
      <AdminDashboardView
        activeTab="projects"
        onTabChange={() => undefined}
        search=""
        onSearchChange={() => undefined}
        items={[]}
        isLoading={false}
        isError
      />
    );
    expect(markup).toContain('Administration data could not be loaded');
    expect(markup).toContain('role="alert"');
  });
});
