import { CheckCircle2, MessageCircleQuestion, PlayCircle, Radio } from 'lucide-react';
import FeatureCard from './feature-card';
import LandingSection from './landing-section';
import WorkerPreview from './previews/worker-preview';
import SectionHeading from './section-heading';
import { translate } from '@/i18n';

const capabilities = [
  {
    icon: PlayCircle,
    get title() {
      return translate('landing:auto.preview_before_dispatch');
    },
    get description() {
      return translate('landing:auto.review_the_generated_prompt_selected_agent_model');
    },
  },
  {
    icon: MessageCircleQuestion,
    get title() {
      return translate('landing:auto.answer_agent_questions');
    },
    get description() {
      return translate('landing:auto.keep_worker_questions_and_human_answers_attached');
    },
  },
  {
    icon: CheckCircle2,
    get title() {
      return translate('landing:auto.follow_job_status');
    },
    get description() {
      return translate('landing:auto.see_online_state_progress_terminal_output_and');
    },
  },
];

export default function RemoteWorkersSection() {
  return (
    <LandingSection id="remote-workers" muted>
      <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <div>
          <SectionHeading
            align="left"
            eyebrow={translate('landing:auto.remote_workers')}
            title={translate('landing:auto.coding_agents_with_visible_context')}
            description={translate('landing:auto.dispatch_sdd_work_to_connected_agents_while')}
            className="mb-7"
          />
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1.5 text-sm font-medium text-emerald-700 dark:text-emerald-400">
            <Radio className="h-4 w-4" aria-hidden="true" />
            {translate('landing:auto.live_worker_presence')}
          </div>
          <WorkerPreview />
        </div>
        <div className="grid gap-4">
          {capabilities.map((capability) => (
            <FeatureCard key={capability.title} {...capability} />
          ))}
        </div>
      </div>
    </LandingSection>
  );
}
