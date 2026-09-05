import { Code2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useCurrentUser } from '@/hooks/use-auth';
import LandingContainer from './landing-container';
import LandingCta from './landing-cta';
import { translate } from '@/i18n';

const productLinks = () =>
  [
    [translate('landing:auto.features'), '#features'],
    [translate('landing:auto.how_it_works'), '#how-it-works'],
    [translate('landing:auto.for_teams'), '#for-teams'],
    [translate('landing:auto.remote_workers'), '#remote-workers'],
  ] as const;

export default function FooterSection() {
  const { data: user, isLoading } = useCurrentUser();
  return (
    <>
      <section className="bg-gradient-to-r from-primary to-indigo-600 py-16 text-primary-foreground">
        <LandingContainer className="text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">
            {translate('landing:auto.ready_to_connect_stories_and_delivery')}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/80">
            {translate('landing:auto.bring_documentation_review_collaboration_and_coding_agents')}
          </p>
          <div className="mt-8 flex justify-center">
            <LandingCta inverted />
          </div>
        </LandingContainer>
      </section>
      <footer className="bg-zinc-950 py-12 text-zinc-300">
        <LandingContainer>
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <Link to="/" className="inline-flex items-center gap-2 text-white">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-sm font-bold">
                  S
                </span>
                <span className="text-lg font-bold">SDD Flow</span>
              </Link>
              <p className="mt-4 max-w-xs text-sm leading-6 text-zinc-400">
                {translate('landing:auto.story_driven_development_coordinated_in_the_cloud')}
              </p>
            </div>
            <FooterGroup title={translate('landing:auto.product')} links={productLinks()} />
            <FooterGroup
              title={translate('landing:auto.resources')}
              links={[
                [translate('landing:auto.open_source'), '#open-source'],
                [translate('landing:auto.privacy'), '/privacy'],
              ]}
            />
            <div>
              <h3 className="text-sm font-semibold text-white">
                {translate('landing:auto.account')}
              </h3>
              <div className="mt-4 flex flex-col items-start gap-3 text-sm text-zinc-400">
                {isLoading ? (
                  <span>{translate('landing:auto.checking_session')}</span>
                ) : user ? (
                  <Link to="/tenants" className="hover:text-white">
                    {translate('landing:auto.open_app')}
                  </Link>
                ) : (
                  <>
                    <Link to="/login" className="hover:text-white">
                      {translate('landing:auto.log_in')}
                    </Link>
                    <Link to="/register" className="hover:text-white">
                      {translate('landing:auto.create_account')}
                    </Link>
                  </>
                )}
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 hover:text-white"
                >
                  <Code2 className="h-4 w-4" />
                  GitHub
                </a>
              </div>
            </div>
          </div>
          <div className="mt-10 border-t border-zinc-800 pt-6 text-sm text-zinc-500">
            {translate('landing:auto.2026_sdd_flow_open_source_software')}
          </div>
        </LandingContainer>
      </footer>
    </>
  );
}

function FooterGroup({
  title,
  links,
}: {
  title: string;
  links: readonly (readonly [string, string])[];
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm text-zinc-400">
        {links.map(([label, href]) => (
          <li key={label}>
            {href.startsWith('/') ? (
              <Link to={href} className="hover:text-white">
                {label}
              </Link>
            ) : (
              <a href={href} className="hover:text-white">
                {label}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
