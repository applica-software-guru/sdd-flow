import { Code2, Package, Terminal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import LandingSection from './landing-section';
import SectionHeading from './section-heading';

const technologies = ['React', 'TypeScript', 'FastAPI', 'MongoDB', 'Tailwind CSS', 'shadcn/ui'];

export default function OpenSourceSection() {
  return (
    <LandingSection id="open-source">
      <div className="mx-auto max-w-3xl text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <Code2 className="h-8 w-8" aria-hidden="true" />
        </div>
        <SectionHeading
          eyebrow="Open source"
          title="Inspect it, run it, improve it"
          description="SDD Flow is built in the open with a typed React frontend, FastAPI backend, and the same SDD workflow it helps teams manage."
        />
        <div className="flex flex-col justify-center gap-3 sm:flex-row">
          <Button asChild size="lg" variant="outline">
            <a href="https://github.com" target="_blank" rel="noreferrer">
              <Code2 className="h-4 w-4" />
              View source
            </a>
          </Button>
          <Button asChild size="lg" variant="outline">
            <a href="#how-it-works">
              <Terminal className="h-4 w-4" />
              CLI workflow
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
