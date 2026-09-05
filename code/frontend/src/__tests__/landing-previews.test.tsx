import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import DashboardPreview from '@/components/landing/previews/dashboard-preview';
import ProjectOverviewPreview from '@/components/landing/previews/project-overview-preview';
import SupportingPreview from '@/components/landing/previews/supporting-preview';
import WorkItemPreview from '@/components/landing/previews/work-item-preview';
import WorkerPreview from '@/components/landing/previews/worker-preview';

describe('landing product previews', () => {
  it('represents the tenant dashboard shown before project selection', () => {
    const markup = renderToStaticMarkup(<DashboardPreview />);
    expect(markup).toContain('Tenant project dashboard preview');
    expect(markup).toContain('Manage your projects and track progress');
    expect(markup).toContain('Choose a project from the dashboard');
    expect(markup).toContain('Hello Project');
    expect(markup).not.toContain('Change Requests');
  });

  it('represents the overview shown after selecting a project', () => {
    const markup = renderToStaticMarkup(<ProjectOverviewPreview />);
    expect(markup).toContain('Selected project overview preview');
    expect(markup).toContain('Inside Hello Project');
    expect(markup).toContain('Change Requests');
    expect(markup).toContain('Documents');
    expect(markup).toContain('Workers Online');
    expect(markup).toContain('Recent Bugs');
  });

  it('shows the shared work-item collaboration concepts', () => {
    const markup = renderToStaticMarkup(<WorkItemPreview />);
    expect(markup).toContain('Shared work-item collaboration preview');
    expect(markup).toContain('Assignment');
    expect(markup).toContain('Latest discussion');
    expect(markup).toContain('Start review');
  });

  it('shows current worker, docs, and structured audit concepts', () => {
    const markup = renderToStaticMarkup(
      <>
        <WorkerPreview />
        <SupportingPreview />
      </>
    );
    expect(markup).toContain('Remote worker orchestration preview');
    expect(markup).toContain('Applying CR-038');
    expect(markup).toContain('product/features/theme.md');
    expect(markup).toContain('Previous status');
    expect(markup).toContain('New status');
  });
});
