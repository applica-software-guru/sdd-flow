import { Link } from 'react-router-dom';

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-blue-50 via-white to-slate-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800">
      {/* Decorative blobs */}
      <div className="pointer-events-none absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-blue-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -right-40 top-20 h-[400px] w-[400px] rounded-full bg-indigo-400/10 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-4 pb-20 pt-20 sm:px-6 sm:pb-24 sm:pt-28 lg:px-8 lg:pb-32 lg:pt-36">
        <div className="mx-auto max-w-4xl text-center">
          <div className="animate-fade-in-up">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
              </svg>
              Open Source
            </span>
          </div>

          <h1 className="mt-6 animate-fade-in-up text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-5xl lg:text-6xl" style={{ animationDelay: '0.1s', animationFillMode: 'both' }}>
            Story Driven Development,{' '}
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              managed in the cloud
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl animate-fade-in-up text-lg text-slate-600 dark:text-slate-400 sm:text-xl" style={{ animationDelay: '0.2s', animationFillMode: 'both' }}>
            The companion platform for the SDD CLI. Manage change requests, track bugs, collaborate with your team, and keep your documentation in sync.
          </p>

          <div className="mt-10 flex animate-fade-in-up flex-col items-center justify-center gap-4 sm:flex-row" style={{ animationDelay: '0.3s', animationFillMode: 'both' }}>
            <Link
              to="/register"
              className="inline-flex items-center rounded-lg bg-blue-600 px-8 py-3 text-base font-semibold text-white shadow-lg transition-all hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-xl"
            >
              Get Started Free
              <svg className="ml-2 h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
            <a
              href="#features"
              className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-8 py-3 text-base font-semibold text-slate-700 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Learn More
              <svg className="ml-2 h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5L12 21m0 0l-7.5-7.5M12 21V3" />
              </svg>
            </a>
          </div>
        </div>

        {/* Product mockup */}
        <div className="mx-auto mt-16 max-w-5xl animate-fade-in-up sm:mt-20" style={{ animationDelay: '0.4s', animationFillMode: 'both' }}>
          <div className="rounded-2xl border border-slate-200/80 bg-white p-2 shadow-2xl ring-1 ring-slate-900/5 dark:border-slate-700 dark:bg-slate-800 dark:ring-white/5">
            {/* Browser chrome */}
            <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3 dark:border-slate-700">
              <div className="flex gap-1.5">
                <div className="h-3 w-3 rounded-full bg-red-400" />
                <div className="h-3 w-3 rounded-full bg-yellow-400" />
                <div className="h-3 w-3 rounded-full bg-green-400" />
              </div>
              <div className="ml-2 flex-1 rounded-md bg-slate-100 px-3 py-1 text-center text-xs text-slate-500 dark:bg-slate-700 dark:text-slate-400">
                app.sddflow.com
              </div>
            </div>

            {/* Simulated dashboard */}
            <div className="p-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <div className="h-4 w-32 rounded bg-slate-200 dark:bg-slate-700" />
                  <div className="mt-2 h-3 w-48 rounded bg-slate-100 dark:bg-slate-700/50" />
                </div>
                <div className="h-8 w-24 rounded-lg bg-blue-600" />
              </div>

              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Open CRs', value: '12', color: 'bg-indigo-50 border-indigo-200 dark:bg-indigo-900/20 dark:border-indigo-800' },
                  { label: 'Open Bugs', value: '5', color: 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' },
                  { label: 'Documents', value: '34', color: 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' },
                ].map((stat) => (
                  <div key={stat.label} className={`rounded-lg border p-4 ${stat.color}`}>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white">{stat.value}</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">{stat.label}</div>
                  </div>
                ))}
              </div>

              <div className="mt-6 space-y-2">
                {[
                  { title: 'CR-014: Update authentication flow', status: 'Approved', statusColor: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
                  { title: 'BUG-007: Search returns stale results', status: 'Open', statusColor: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
                  { title: 'CR-015: Add API rate limiting', status: 'Draft', statusColor: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
                ].map((item) => (
                  <div key={item.title} className="flex items-center justify-between rounded-lg border border-slate-100 px-4 py-3 dark:border-slate-700">
                    <span className="text-sm font-medium text-slate-900 dark:text-white">{item.title}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${item.statusColor}`}>{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
