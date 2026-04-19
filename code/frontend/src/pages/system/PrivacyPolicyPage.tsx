import { Link } from 'react-router-dom';
import LandingNavbar from '../../components/landing/LandingNavbar';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-900">
      <LandingNavbar />

      <main className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Privacy Policy</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Last updated: April 19, 2026</p>

        <div className="mt-10 space-y-10 text-slate-700 dark:text-slate-300">

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">1. Who we are</h2>
            <p className="mt-3 text-sm leading-relaxed">
              SDD Flow is operated by <strong>Applica Software Guru</strong> (<a href="mailto:bruno.fortunato@applica.guru" className="text-blue-600 hover:underline dark:text-blue-400">bruno.fortunato@applica.guru</a>).
              This policy explains what data we collect, why, and your rights over it.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">2. Data we collect</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              <li><strong>Account data</strong>: email address, name, and hashed password when you register.</li>
              <li><strong>Project data</strong>: SDD documentation files (docs, change requests, bugs) you upload or sync via the CLI.</li>
              <li><strong>Usage data</strong>: basic server logs (IP address, timestamps, HTTP status codes) for security and reliability purposes.</li>
              <li><strong>Authentication tokens</strong>: short-lived JWT access tokens and 7-day refresh tokens stored in HTTP-only cookies.</li>
            </ul>
            <p className="mt-3 text-sm leading-relaxed">
              We do not collect payment information, run advertising trackers, or sell your data to third parties.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">3. How we use your data</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              <li>To provide and operate the SDD Flow service.</li>
              <li>To authenticate you and keep your session secure.</li>
              <li>To store and sync your SDD project documentation across devices.</li>
              <li>To dispatch AI agent jobs to your registered worker machines when you use the remote worker feature.</li>
              <li>To send transactional emails (password reset, invitations) when you request them.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">4. Data storage and security</h2>
            <p className="mt-3 text-sm leading-relaxed">
              Data is stored in a PostgreSQL database hosted on Google Cloud (Cloud Run + Cloud SQL).
              All traffic is encrypted in transit via HTTPS/TLS. Passwords are hashed and never stored in plain text.
              We apply the principle of least privilege: each component only accesses the data it needs.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">5. Data retention</h2>
            <p className="mt-3 text-sm leading-relaxed">
              Your data is retained as long as your account is active. If you delete your account or a project,
              the associated data is permanently removed from our systems within 30 days.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">6. Third-party services</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed">
              <li><strong>Google OAuth</strong>: if you sign in with Google, we receive your email and name from Google. We do not store your Google password.</li>
              <li><strong>Google Cloud</strong>: infrastructure provider for hosting and database.</li>
              <li><strong>Cloudflare Pages</strong>: CDN and hosting for the frontend.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">7. Your rights</h2>
            <p className="mt-3 text-sm leading-relaxed">
              You have the right to access, correct, export, or delete your personal data at any time.
              To exercise these rights, contact us at{' '}
              <a href="mailto:bruno.fortunato@applica.guru" className="text-blue-600 hover:underline dark:text-blue-400">
                bruno.fortunato@applica.guru
              </a>
              . We will respond within 30 days.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">8. Cookies</h2>
            <p className="mt-3 text-sm leading-relaxed">
              We use HTTP-only cookies solely for authentication (access and refresh tokens).
              We do not use tracking or advertising cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">9. Changes to this policy</h2>
            <p className="mt-3 text-sm leading-relaxed">
              We may update this policy from time to time. Changes will be posted on this page with an updated date.
              Continued use of the service after changes constitutes acceptance of the updated policy.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">10. Contact</h2>
            <p className="mt-3 text-sm leading-relaxed">
              For any privacy-related questions, contact:{' '}
              <a href="mailto:bruno.fortunato@applica.guru" className="text-blue-600 hover:underline dark:text-blue-400">
                bruno.fortunato@applica.guru
              </a>
            </p>
          </section>

        </div>

        <div className="mt-16 border-t border-slate-200 pt-8 dark:border-slate-700">
          <Link to="/" className="text-sm text-blue-600 hover:underline dark:text-blue-400">
            ← Back to home
          </Link>
        </div>
      </main>
    </div>
  );
}
