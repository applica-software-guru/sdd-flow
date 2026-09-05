import { Bot, Bug, FileText, GitPullRequest, History, Users } from 'lucide-react';
import FeatureCard from './feature-card';
import LandingSection from './landing-section';
import ProjectOverviewPreview from './previews/project-overview-preview';
import SupportingPreview from './previews/supporting-preview';
import SectionHeading from './section-heading';

const features = [
  {
    icon: GitPullRequest,
    title: 'Change requests',
    description:
      'Move proposed changes from draft through review and application with an explicit, auditable workflow.',
  },
  {
    icon: Bug,
    title: 'Bug tracking',
    description:
      'Capture defects with severity, assignment, transitions, comments, and worker-assisted enrichment.',
  },
  {
    icon: FileText,
    title: 'Living documentation',
    description:
      'Browse and edit the complete product and system documentation tree with rich Markdown rendering.',
  },
  {
    icon: Bot,
    title: 'Remote workers',
    description:
      'Connect coding agents, preview jobs, answer questions, and follow execution from the project workspace.',
  },
  {
    icon: Users,
    title: 'Team collaboration',
    description:
      'Keep authors, assignees, discussion, and tenant roles visible wherever work is coordinated.',
  },
  {
    icon: History,
    title: 'Readable audit history',
    description:
      'Review human-readable events and expand structured details only when an event has meaningful data.',
  },
];

export default function FeaturesSection() {
  return (
    <LandingSection id="features">
      <SectionHeading
        eyebrow="One shared workspace"
        title="From story to implementation"
        description="SDD Flow connects specifications, work items, documentation, and coding agents without hiding the state of delivery."
      />
      <div className="mx-auto mb-12 max-w-5xl">
        <p className="mb-3 text-center text-sm font-medium text-muted-foreground">
          Select a project to open its overview and project navigation.
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
