import { Code2, Package, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import LandingSection from './landing-section';
import SectionHeading from './section-heading';
import { translate } from '@/i18n';

const technologies = ['React', 'TypeScript', 'FastAPI', 'MongoDB', 'Tailwind CSS', 'shadcn/ui'];

export default function OpenSourceSection() {
  return (
    <LandingSection id="open-source">
      <div className="mx-auto max-w-3xl text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <Code2 className="h-8 w-8" aria-hidden="true" />
        </div>
        <SectionHeading
          eyebrow={translate('landing:auto.open_source')}
          title={translate('landing:auto.inspect_it_run_it_improve_it')}
          description={translate('landing:auto.sdd_flow_is_built_in_the_open')}
        />
        <div className="flex flex-col justify-center gap-3 sm:flex-row">
          <Button asChild size="lg" variant="outline">
            <a href="https://github.com" target="_blank" rel="noreferrer">
              <Code2 className="h-4 w-4" />
              {translate('landing:auto.view_source')}
            </a>
          </Button>
          <Button asChild size="lg" variant="outline">
            <a href="#how-it-works">
              <Terminal className="h-4 w-4" />
              {translate('landing:auto.cli_workflow')}
            </a>
          </Button>
        </div>
        <div className="mt-10 flex flex-wrap justify-center gap-2">
          {technologies.map((technology) => (
            <span
              key={technology}
              className="inline-flex items-center gap-1.5 rounded-full border bg-muted/40 px-3 py-1.5 text-sm font-medium text-muted-foreground"
            >
              {technology === 'shadcn/ui' && <Package className="h-3.5 w-3.5" aria-hidden="true" />}
              {technology}
            </span>
          ))}
        </div>
      </div>
    </LandingSection>
  );
}
