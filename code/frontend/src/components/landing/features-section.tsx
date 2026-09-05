import { Bot, Bug, FileText, GitPullRequest, History, Users } from 'lucide-react';
import FeatureCard from './feature-card';
import LandingSection from './landing-section';
import ProjectOverviewPreview from './previews/project-overview-preview';
import SupportingPreview from './previews/supporting-preview';
import SectionHeading from './section-heading';
import { translate } from '@/i18n';

const features = [
  {
    icon: GitPullRequest,
    get title() {
      return translate('landing:auto.change_requests_2');
    },
    get description() {
      return translate('landing:auto.move_proposed_changes_from_draft_through_review');
    },
  },
  {
    icon: Bug,
    get title() {
      return translate('landing:auto.bug_tracking');
    },
    get description() {
      return translate(
        'landing:auto.capture_defects_with_severity_assignment_transitions_comments'
      );
    },
  },
  {
    icon: FileText,
    get title() {
      return translate('landing:auto.living_documentation');
    },
    get description() {
      return translate('landing:auto.browse_and_edit_the_complete_product_and');
    },
  },
  {
    icon: Bot,
    get title() {
      return translate('landing:auto.remote_workers');
    },
    get description() {
      return translate('landing:auto.connect_coding_agents_preview_jobs_answer_questions');
    },
  },
  {
    icon: Users,
    get title() {
      return translate('landing:auto.team_collaboration');
    },
    get description() {
      return translate('landing:auto.keep_authors_assignees_discussion_and_tenant_roles');
    },
  },
  {
    icon: History,
    get title() {
      return translate('landing:auto.readable_audit_history');
    },
    get description() {
      return translate('landing:auto.review_human_readable_events_and_expand_structured');
    },
  },
];

export default function FeaturesSection() {
  return (
    <LandingSection id="features">
      <SectionHeading
        eyebrow={translate('landing:auto.one_shared_workspace')}
        title={translate('landing:auto.from_story_to_implementation')}
        description={translate(
          'landing:auto.sdd_flow_connects_specifications_work_items_documentation'
        )}
      />
      <div className="mx-auto mb-12 max-w-5xl">
        <p className="mb-3 text-center text-sm font-medium text-muted-foreground">
          {translate('landing:auto.select_a_project_to_open_its_overview')}
        </p>
        <ProjectOverviewPreview />
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <FeatureCard key={feature.title} {...feature} />
        ))}
      </div>
      <div className="mx-auto mt-10 max-w-4xl">
        <SupportingPreview />
      </div>
    </LandingSection>
  );
}
