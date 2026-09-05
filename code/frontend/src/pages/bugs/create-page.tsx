import { useNavigate } from 'react-router-dom';
import BackLink from '@/components/shared/back-link';
import PageHeader from '@/components/shared/page-header';
import PageContainer from '@/components/page-container';
import CreateWorkItemForm from '@/features/work-items/create-work-item-form';
import { useCreateBug } from '@/hooks/use-bugs';
import { useProjectRoute } from '@/hooks/use-project-route';
import { useTenantMembers } from '@/hooks/use-tenants';

export default function CreatePage() {
  const route = useProjectRoute();
  const navigate = useNavigate();
  const createBug = useCreateBug(route?.tenantId ?? '', route?.projectId ?? '');
  const { data: members } = useTenantMembers(route?.tenantId);
  if (!route)
    return (
      <PageContainer>
        <p role="alert">Project route is incomplete.</p>
      </PageContainer>
    );
  const backTo = `/tenants/${route.tenantId}/projects/${route.projectId}/bugs`;

  return (
    <PageContainer className="space-y-6">
      <BackLink to={backTo}>Back to Bugs</BackLink>
      <div>
        <PageHeader title="Report a Bug" />
        <CreateWorkItemForm
          backTo={backTo}
          filenamePrefix="bugs"
          titlePlaceholder="Brief description of the bug"
          submitLabel="Report bug"
          pendingLabel="Reporting…"
          errorMessage="Failed to report bug. Please try again."
          members={members}
          pending={createBug.isPending}
          failed={createBug.isError}
          withSeverity
          onSubmit={async (values) => {
            try {
              const bug = await createBug.mutateAsync({
                ...values,
                severity: values.severity ?? 'minor',
              });
              navigate(`${backTo}/${bug.id}`);
            } catch {
              /* mutation state renders the error */
            }
          }}
        />
      </div>
    </PageContainer>
  );
}
