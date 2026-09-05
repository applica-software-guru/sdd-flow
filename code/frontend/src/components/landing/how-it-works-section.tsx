import { CloudUpload, GitPullRequest, TerminalSquare } from 'lucide-react';
import LandingSection from './landing-section';
import SectionHeading from './section-heading';
import { translate } from '@/i18n';

const steps = () => [
  {
    icon: TerminalSquare,
    get title() {
      return translate('landing:auto.connect_the_cli');
    },
    description: <>{translate('landing:auto.install_the_sdd_cli_and_connect_a')}</>,
  },
  {
    icon: CloudUpload,
    get title() {
      return translate('landing:auto.synchronize_stories');
    },
    description: (
      <>{translate('landing:auto.push_product_and_system_documentation_while_preserving')}</>
    ),
  },
  {
    icon: GitPullRequest,
    get title() {
      return translate('landing:auto.coordinate_delivery');
    },
    description: (
      <>{translate('landing:auto.review_changes_bugs_assignments_discussion_and_coding')}</>
    ),
  },
];

export default function HowItWorksSection() {
  return (
    <LandingSection id="how-it-works" muted>
      <SectionHeading
        eyebrow={translate('landing:auto.simple_workflow')}
        title={translate('landing:auto.documentation_and_delivery_stay_connected')}
        description={translate('landing:auto.the_cli_and_web_workspace_share_the')}
      />
      <ol className="relative grid gap-8 lg:grid-cols-3 lg:gap-12">
        {steps().map((step, index) => (
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
