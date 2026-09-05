import { ArrowDown, Sparkles } from 'lucide-react';
import LandingContainer from './landing-container';
import LandingCta from './landing-cta';
import DashboardPreview from './previews/dashboard-preview';
import { translate } from '@/i18n';

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-primary/10 via-background to-muted/40">
      <div className="pointer-events-none absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-40 top-20 h-[400px] w-[400px] rounded-full bg-indigo-500/10 blur-3xl" />
      <LandingContainer className="relative pb-20 pt-20 sm:pb-24 sm:pt-28 lg:pb-28 lg:pt-32">
        <div className="mx-auto max-w-4xl text-center">
          <div className="animate-fade-in-up motion-reduce:animate-none">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
              <Sparkles className="h-4 w-4" aria-hidden="true" />{' '}
              {translate('landing:auto.open_source')}
            </span>
          </div>
          <h1
            className="animate-fade-in-up mt-6 text-4xl font-bold tracking-tight text-foreground motion-reduce:animate-none sm:text-5xl lg:text-6xl"
            style={{ animationDelay: '0.1s', animationFillMode: 'both' }}
          >
            {translate('landing:auto.story_driven_development')}{' '}
            <span className="bg-gradient-to-r from-primary to-indigo-500 bg-clip-text text-transparent">
              {translate('landing:auto.managed_in_the_cloud')}
            </span>
          </h1>
          <p
            className="animate-fade-in-up mx-auto mt-6 max-w-2xl text-lg text-muted-foreground motion-reduce:animate-none sm:text-xl"
            style={{ animationDelay: '0.2s', animationFillMode: 'both' }}
          >
            {translate('landing:auto.manage_change_requests_track_bugs_collaborate_with')}
          </p>
          <div
            className="animate-fade-in-up mt-10 flex flex-col items-center justify-center gap-4 motion-reduce:animate-none sm:flex-row"
            style={{ animationDelay: '0.3s', animationFillMode: 'both' }}
          >
            <LandingCta />
            <a
              href="#features"
              className="inline-flex min-h-11 min-w-44 items-center justify-center gap-2 rounded-md border bg-card px-6 text-sm font-semibold text-foreground shadow-sm transition-transform hover:-translate-y-0.5 hover:bg-accent motion-reduce:transform-none"
            >
              {translate('landing:auto.explore_features')}
              <ArrowDown className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>
        </div>
        <div
          className="animate-fade-in-up mx-auto mt-16 max-w-5xl motion-reduce:animate-none sm:mt-20"
          style={{ animationDelay: '0.4s', animationFillMode: 'both' }}
        >
          <DashboardPreview />
        </div>
      </LandingContainer>
    </section>
  );
}
