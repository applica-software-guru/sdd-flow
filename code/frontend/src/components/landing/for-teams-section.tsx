import { Check, MessageSquare, UserRoundCheck } from 'lucide-react';
import LandingSection from './landing-section';
import WorkItemPreview from './previews/work-item-preview';
import SectionHeading from './section-heading';

const benefits = [
  'See authors, assignees, status, severity, and discussion in one place',
  'Use the same collaboration flow for bugs and change requests',
  'Keep assignment history and audit history explicit',
  'Hand work to connected coding agents without losing context',
];

export default function ForTeamsSection() {
  return (
    <LandingSection id="for-teams">
      <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
        <div>
          <SectionHeading
            align="left"
            eyebrow="Built for collaboration"
            title="A work item tells the whole story"
            description="Shared components keep the important context consistent from a project overview to detailed review."
            className="mb-7"
          />
          <ul className="space-y-4">
            {benefits.map((benefit) => (
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
              Clear ownership
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5">
              <MessageSquare className="h-4 w-4 text-primary" />
              Focused discussion
            </span>
          </div>
        </div>
        <WorkItemPreview />
      </div>
    </LandingSection>
  );
}
