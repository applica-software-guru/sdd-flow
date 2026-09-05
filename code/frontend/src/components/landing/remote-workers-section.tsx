import { CheckCircle2, MessageCircleQuestion, PlayCircle, Radio } from 'lucide-react';
import FeatureCard from './feature-card';
import LandingSection from './landing-section';
import WorkerPreview from './previews/worker-preview';
import SectionHeading from './section-heading';

const capabilities = [
  {
    icon: PlayCircle,
    title: 'Preview before dispatch',
    description:
      'Review the generated prompt, selected agent, model, and target before creating a job.',
  },
  {
    icon: MessageCircleQuestion,
    title: 'Answer agent questions',
    description: 'Keep worker questions and human answers attached to the running job.',
  },
  {
    icon: CheckCircle2,
    title: 'Follow job status',
    description:
      'See online state, progress, terminal output, and completion without leaving the project.',
  },
];

export default function RemoteWorkersSection() {
  return (
    <LandingSection id="remote-workers" muted>
      <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <div>
          <SectionHeading
            align="left"
            eyebrow="Remote workers"
            title="Coding agents with visible context"
            description="Dispatch SDD work to connected agents while the project remains the source of truth."
            className="mb-7"
          />
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1.5 text-sm font-medium text-emerald-700 dark:text-emerald-400">
            <Radio className="h-4 w-4" aria-hidden="true" />
            Live worker presence
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
