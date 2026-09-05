import { useNavigate } from 'react-router-dom';
import BackLink from '@/components/shared/back-link';
import PageHeader from '@/components/shared/page-header';
import PageContainer from '@/components/page-container';
import CreateWorkItemForm from '@/features/work-items/create-work-item-form';
import { useCreateCR } from '@/hooks/use-change-requests';
import { useProjectRoute } from '@/hooks/use-project-route';
import { useTenantMembers } from '@/hooks/use-tenants';

export default function CreatePage() {
  const route = useProjectRoute();
  const navigate = useNavigate();
  const createCR = useCreateCR(route?.tenantId ?? '', route?.projectId ?? '');
  const { data: members } = useTenantMembers(route?.tenantId);
  if (!route)
    return (
      <PageContainer>
        <p role="alert">Project route is incomplete.</p>
      </PageContainer>
    );
  const backTo = `/tenants/${route.tenantId}/projects/${route.projectId}/crs`;

  return (
    <PageContainer className="space-y-6">
      <BackLink to={backTo}>Back to CRs</BackLink>
      <div>
        <PageHeader title="New Change Request" />
        <CreateWorkItemForm
          backTo={backTo}
          filenamePrefix="change-requests"
          titlePlaceholder="Brief description of the change"
          submitLabel="Create change request"
          pendingLabel="Creating…"
          errorMessage="Failed to create change request. Please try again."
          members={members}
          pending={createCR.isPending}
          failed={createCR.isError}
          onSubmit={async (values) => {
            try {
              const cr = await createCR.mutateAsync(values);
              navigate(`${backTo}/${cr.id}`);
            } catch {
              /* mutation state renders the error */
            }
          }}
        />
      </div>
    </PageContainer>
  );
}
