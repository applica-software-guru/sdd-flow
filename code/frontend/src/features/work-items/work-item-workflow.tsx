import AssignmentPanel, { AssignmentHistory } from '@/components/assignment-panel';
import { Button } from '@/components/ui/button';
import type { AssignmentHistoryEntry, TenantMember, UserBrief } from '@/types';
import { translate } from '@/i18n';

interface WorkItemWorkflowProps<TStatus extends string> {
  title: string;
  author?: UserBrief | null;
  assigneeId: string | null;
  members: TenantMember[];
  history?: AssignmentHistoryEntry[];
  transitions: TStatus[];
  pending: boolean;
  assigning: boolean;
  onTransition: (status: TStatus) => void;
  onAssign: (assigneeId: string | null) => void;
}

function formatStatus(status: string) {
  const fallback = status.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
  return translate(`common:status.${status}`, { defaultValue: fallback });
}

export default function WorkItemWorkflow<TStatus extends string>(
  props: WorkItemWorkflowProps<TStatus>
) {
  return (
    <div className="border-t px-6 py-4">
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-sm font-medium">{translate('common:auto.transition_to')}</p>
          {props.transitions.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {props.transitions.map((status) => (
                <Button
                  key={status}
                  variant="outline"
                  size="sm"
                  onClick={() => props.onTransition(status)}
                  disabled={props.pending}
                >
                  {formatStatus(status)}
                </Button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              {translate('common:auto.no_transition_available')}
            </p>
          )}
        </div>
        <div className="lg:border-l lg:pl-6">
          <AssignmentPanel
            author={props.author}
            assigneeId={props.assigneeId}
            members={props.members}
            history={props.history}
            onAssign={props.onAssign}
            assigning={props.assigning}
          />
        </div>
      </div>
      <AssignmentHistory history={props.history} entityLabel={props.title} />
    </div>
  );
}
