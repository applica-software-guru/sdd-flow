import { Code2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useCurrentUser } from '@/hooks/use-auth';
import LandingContainer from './landing-container';
import LandingCta from './landing-cta';

const productLinks = [
  ['Features', '#features'],
  ['How it works', '#how-it-works'],
  ['For teams', '#for-teams'],
  ['Remote workers', '#remote-workers'],
] as const;

export default function FooterSection() {
  const { data: user, isLoading } = useCurrentUser();
  return (
    <>
      <section className="bg-gradient-to-r from-primary to-indigo-600 py-16 text-primary-foreground">
        <LandingContainer className="text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">Ready to connect stories and delivery?</h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/80">
            Bring documentation, review, collaboration, and coding agents into one explicit
            workflow.
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
                Story Driven Development, coordinated in the cloud.
              </p>
            </div>
            <FooterGroup title="Product" links={productLinks} />
            <FooterGroup
              title="Resources"
              links={[
                ['Open source', '#open-source'],
                ['Privacy', '/privacy'],
              ]}
            />
            <div>
              <h3 className="text-sm font-semibold text-white">Account</h3>
              <div className="mt-4 flex flex-col items-start gap-3 text-sm text-zinc-400">
                {isLoading ? (
                  <span>Checking session…</span>
                ) : user ? (
                  <Link to="/tenants" className="hover:text-white">
                    Open app
                  </Link>
                ) : (
                  <>
                    <Link to="/login" className="hover:text-white">
                      Log in
                    </Link>
                    <Link to="/register" className="hover:text-white">
                      Create account
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
            © 2026 SDD Flow. Open source software.
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
