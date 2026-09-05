import { useNavigate } from 'react-router-dom';
import BackLink from '@/components/shared/back-link';
import PageHeader from '@/components/shared/page-header';
import PageContainer from '@/components/page-container';
import CreateWorkItemForm from '@/features/work-items/create-work-item-form';
import { useCreateCR } from '@/hooks/use-change-requests';
import { useProjectRoute } from '@/hooks/use-project-route';
import { useTenantMembers } from '@/hooks/use-tenants';
import { translate } from '@/i18n';

export default function CreatePage() {
  const route = useProjectRoute();
  const navigate = useNavigate();
  const createCR = useCreateCR(route?.tenantId ?? '', route?.projectId ?? '');
  const { data: members } = useTenantMembers(route?.tenantId);
  if (!route)
    return (
      <PageContainer>
        <p role="alert">{translate('change-requests:auto.project_route_is_incomplete')}</p>
      </PageContainer>
    );
  const backTo = `/tenants/${route.tenantId}/projects/${route.projectId}/crs`;

  return (
    <PageContainer className="space-y-6">
      <BackLink to={backTo}>{translate('change-requests:auto.back_to_crs')}</BackLink>
      <div>
        <PageHeader title={translate('change-requests:auto.new_change_request')} />
        <CreateWorkItemForm
          backTo={backTo}
          filenamePrefix="change-requests"
          titlePlaceholder={translate('change-requests:auto.brief_description_of_the_change')}
          submitLabel={translate('change-requests:auto.create_change_request')}
          pendingLabel={translate('change-requests:auto.creating')}
          errorMessage={translate(
            'change-requests:auto.failed_to_create_change_request_please_try_again'
          )}
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
