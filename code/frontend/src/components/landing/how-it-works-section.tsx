import { CloudUpload, GitPullRequest, TerminalSquare } from 'lucide-react';
import LandingSection from './landing-section';
import SectionHeading from './section-heading';

const steps = [
  {
    icon: TerminalSquare,
    title: 'Connect the CLI',
    description: <>Install the SDD CLI and connect a project with a scoped API key.</>,
  },
  {
    icon: CloudUpload,
    title: 'Synchronize stories',
    description: (
      <>Push product and system documentation while preserving SDD status and references.</>
    ),
  },
  {
    icon: GitPullRequest,
    title: 'Coordinate delivery',
    description: (
      <>
        Review changes, bugs, assignments, discussion, and coding-agent jobs from the shared
        project.
      </>
    ),
  },
];

export default function HowItWorksSection() {
  return (
    <LandingSection id="how-it-works" muted>
      <SectionHeading
        eyebrow="Simple workflow"
        title="Documentation and delivery stay connected"
        description="The CLI and web workspace share the same SDD lifecycle, from a proposed change to synchronized implementation."
      />
      <ol className="relative grid gap-8 lg:grid-cols-3 lg:gap-12">
        {steps.map((step, index) => (
          <li key={step.title} className="relative text-center">
            <div className="relative mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl border bg-card text-primary shadow-lg">
              <step.icon className="h-9 w-9" aria-hidden="true" />
              <span className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground ring-2 ring-background">
                {index + 1}
              </span>
            </div>
            <h3 className="text-lg font-semibold">{step.title}</h3>
            <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
              {step.description}
            </p>
          </li>
        ))}
      </ol>
    </LandingSection>
  );
}
