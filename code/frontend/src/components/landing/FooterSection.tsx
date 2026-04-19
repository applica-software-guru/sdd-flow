import { Link } from 'react-router-dom';

export default function FooterSection() {
  return (
    <section>
      {/* CTA Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 py-16 px-4">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ready to streamline your development workflow?
          </h2>
          <p className="mt-4 text-lg text-blue-100">
            Start managing your SDD projects in the cloud today. Free to get started.
          </p>
          <Link
            to="/register"
            className="mt-8 inline-flex items-center rounded-lg bg-white px-8 py-3 text-base font-semibold text-blue-600 shadow-lg transition-all hover:-translate-y-0.5 hover:shadow-xl"
          >
            Get Started Free
            <svg className="ml-2 h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-slate-900 dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {/* Brand */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
                  S
                </div>
                <span className="text-lg font-bold text-white">SDD Flow</span>
              </div>
              <p className="mt-3 text-sm text-slate-400">
                Story Driven Development, managed in the cloud.
              </p>
            </div>

            {/* Product */}
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Product</h3>
              <ul className="mt-4 space-y-2">
                <li><a href="#features" className="text-sm text-slate-400 hover:text-white transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="text-sm text-slate-400 hover:text-white transition-colors">How it Works</a></li>
                <li><a href="#open-source" className="text-sm text-slate-400 hover:text-white transition-colors">Open Source</a></li>
              </ul>
            </div>

            {/* Developers */}
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Developers</h3>
              <ul className="mt-4 space-y-2">
                <li><a href="https://github.com/applica-software-guru/sdd" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-400 hover:text-white transition-colors">SDD CLI</a></li>
                <li><a href="https://github.com/applica-software-guru/sdd-flow" target="_blank" rel="noopener noreferrer" className="text-sm text-slate-400 hover:text-white transition-colors">GitHub</a></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Account</h3>
              <ul className="mt-4 space-y-2">
                <li><Link to="/login" className="text-sm text-slate-400 hover:text-white transition-colors">Log in</Link></li>
                <li><Link to="/register" className="text-sm text-slate-400 hover:text-white transition-colors">Sign up</Link></li>
              </ul>
            </div>
          </div>

          <div className="mt-12 border-t border-slate-800 pt-8 flex flex-col items-center gap-2 sm:flex-row sm:justify-between">
            <p className="text-sm text-slate-500">
              &copy; {new Date().getFullYear()} SDD Flow. Open source under MIT License.
            </p>
            <Link to="/privacy" className="text-sm text-slate-500 hover:text-slate-300 transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>
    </section>
  );
}
