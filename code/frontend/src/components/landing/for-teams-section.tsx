import { Check, MessageSquare, UserRoundCheck } from 'lucide-react';
import LandingSection from './landing-section';
import WorkItemPreview from './previews/work-item-preview';
import SectionHeading from './section-heading';
import { translate } from '@/i18n';

const benefits = () => [
  translate('landing:auto.see_authors_assignees_status_severity_and_discussion_in'),
  translate('landing:auto.use_the_same_collaboration_flow_for_bugs_and_change_req'),
  translate('landing:auto.keep_assignment_history_and_audit_history_explicit'),
  translate('landing:auto.hand_work_to_connected_coding_agents_without_losing_con'),
];

export default function ForTeamsSection() {
  return (
    <LandingSection id="for-teams">
      <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <div>
          <SectionHeading
            align="left"
            eyebrow={translate('landing:auto.built_for_collaboration')}
            title={translate('landing:auto.a_work_item_tells_the_whole_story')}
            description={translate(
              'landing:auto.shared_components_keep_the_important_context_consistent'
            )}
            className="mb-7"
          />
          <ul className="space-y-4">
            {benefits().map((benefit) => (
              <li key={benefit} className="flex gap-3 text-sm text-muted-foreground">
                <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Check className="h-4 w-4" aria-hidden="true" />
                </span>
                {benefit}
              </li>
            ))}
          </ul>
          <div className="mt-8 flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5">
              <UserRoundCheck className="h-4 w-4 text-primary" />
              {translate('landing:auto.clear_ownership')}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5">
              <MessageSquare className="h-4 w-4 text-primary" />
              {translate('landing:auto.focused_discussion')}
            </span>
          </div>
        </div>
        <WorkItemPreview />
      </div>
    </LandingSection>
  );
}
