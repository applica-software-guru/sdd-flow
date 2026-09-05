// @vitest-environment jsdom
import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import WorkspaceSwitcher from '@/components/workspace-switcher';
import type { WorkspaceNavigationResponse } from '@/types';

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  params: {} as { tenantId?: string; projectId?: string },
  useWorkspaceNavigation: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => mocks.navigate,
  useParams: () => mocks.params,
}));

vi.mock('@/hooks/use-tenants', () => ({
  useWorkspaceNavigation: () => mocks.useWorkspaceNavigation(),
}));

const navigation: WorkspaceNavigationResponse = {
  tenants: [
    {
      id: 't1',
      name: 'Acme',
      slug: 'acme',
      role: 'admin',
      can_create_project: true,
      projects: [
        { id: 'p1', name: 'Web App', slug: 'web-app', archived_at: null },
        { id: 'p2', name: 'Internal API', slug: 'api', archived_at: null },
      ],
    },
    {
      id: 't2',
      name: 'Beta',
      slug: 'beta',
      role: 'viewer',
      can_create_project: false,
      projects: [{ id: 'p3', name: 'Docs Portal', slug: 'docs', archived_at: null }],
    },
  ],
};

async function openSwitcher() {
  const user = userEvent.setup();
  await user.click(screen.getByRole('button', { name: 'Select tenant or project workspace' }));
  return user;
}

describe('WorkspaceSwitcher', () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    mocks.navigate.mockReset();
    mocks.params = { tenantId: 't1' };
    mocks.useWorkspaceNavigation.mockReturnValue({
      data: navigation,
      isError: false,
      isLoading: false,
    });
  });

  it('navigates to tenant overview from a tenant row', async () => {
    render(<WorkspaceSwitcher />);
    const user = await openSwitcher();

    await user.click(screen.getByText('Tenant overview · acme'));

    expect(mocks.navigate).toHaveBeenCalledWith('/tenants/t1');
  });

  it('navigates directly to a selected project', async () => {
    render(<WorkspaceSwitcher />);
    const user = await openSwitcher();

    await user.click(screen.getByText('Web App'));

    expect(mocks.navigate).toHaveBeenCalledWith('/tenants/t1/projects/p1');
  });

  it('highlights the current project route', async () => {
    mocks.params = { tenantId: 't1', projectId: 'p2' };
    render(<WorkspaceSwitcher />);

    await openSwitcher();
    const projectItem = screen.getByText('Internal API').closest('[role="menuitem"]');

    expect(projectItem?.getAttribute('class')).toContain('bg-accent');
  });

  it('searches projects while preserving the parent tenant context', async () => {
    render(<WorkspaceSwitcher />);
    const user = await openSwitcher();

    await user.type(screen.getByRole('textbox', { name: 'Search tenants or projects' }), 'api');

    expect(screen.getAllByText('Acme').length).toBeGreaterThan(0);
    expect(screen.getByText('Internal API')).toBeTruthy();
    expect(screen.queryByText('Web App')).toBeNull();
    expect(screen.queryByText('Beta')).toBeNull();
  });

  it('shows permission-aware new project action only for the current tenant', async () => {
    const firstView = render(<WorkspaceSwitcher />);
    await openSwitcher();

    expect(screen.getByText('New project')).toBeTruthy();
    firstView.unmount();

    mocks.params = { tenantId: 't2' };
    mocks.navigate.mockReset();
    render(<WorkspaceSwitcher />);
    await openSwitcher();

    const menu = screen.getByRole('menu');
    expect(within(menu).queryByText('New project')).toBeNull();
  });
});
