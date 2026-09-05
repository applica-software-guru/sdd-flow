import { useNavigate } from 'react-router-dom';
import BackLink from '@/components/shared/back-link';
import PageHeader from '@/components/shared/page-header';
import PageContainer from '@/components/page-container';
import CreateWorkItemForm from '@/features/work-items/create-work-item-form';
import { useCreateBug } from '@/hooks/use-bugs';
import { useProjectRoute } from '@/hooks/use-project-route';
import { useTenantMembers } from '@/hooks/use-tenants';
import { translate } from '@/i18n';

export default function CreatePage() {
  const route = useProjectRoute();
  const navigate = useNavigate();
  const createBug = useCreateBug(route?.tenantId ?? '', route?.projectId ?? '');
  const { data: members } = useTenantMembers(route?.tenantId);
  if (!route)
    return (
      <PageContainer>
        <p role="alert">{translate('bugs:auto.project_route_is_incomplete')}</p>
      </PageContainer>
    );
  const backTo = `/tenants/${route.tenantId}/projects/${route.projectId}/bugs`;

  return (
    <PageContainer className="space-y-6">
      <BackLink to={backTo}>{translate('bugs:auto.back_to_bugs')}</BackLink>
      <div>
        <PageHeader title={translate('bugs:auto.report_a_bug')} />
        <CreateWorkItemForm
          backTo={backTo}
          filenamePrefix="bugs"
          titlePlaceholder={translate('bugs:auto.brief_description_of_the_bug')}
          submitLabel={translate('bugs:auto.report_bug_2')}
          pendingLabel={translate('bugs:auto.reporting')}
          errorMessage={translate('bugs:auto.failed_to_report_bug_please_try_again')}
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
