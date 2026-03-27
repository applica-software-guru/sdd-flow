const steps = [
  {
    number: '01',
    title: 'Install the SDD CLI',
    description: 'One command and you\'re ready. The CLI runs on your machine, your CI server, or anywhere you keep your codebase.',
    code: 'npm install -g @applica-software-guru/sdd',
  },
  {
    number: '02',
    title: 'Start a worker',
    description: 'Point it at your project and let it connect. The worker registers itself and waits silently for jobs to arrive.',
    code: 'sdd remote worker --name my-machine',
  },
  {
    number: '03',
    title: 'Assign work from the browser',
    description: 'Open a Change Request or Bug in SDD Flow, hit "Run on Worker", and watch it get handled — no terminal required.',
    code: null,
  },
];

const benefits = [
  {
    title: 'Your code never leaves your machine',
    description: 'The worker runs locally. SDD Flow only sends instructions and receives results — your codebase stays where it is.',
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    title: 'Run multiple workers in parallel',
    description: 'Got a CI box and a local machine? Connect both. SDD Flow distributes jobs across all available workers automatically.',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
      </svg>
    ),
  },
  {
    title: 'Works with any AI agent',
    description: 'Claude, a custom script, or any compatible agent — the worker is model-agnostic. Use what you already have.',
    color: 'text-violet-600 dark:text-violet-400',
    bg: 'bg-violet-100 dark:bg-violet-900/30',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
    ),
  },
  {
    title: 'Full output in the browser',
    description: 'Every message the agent writes streams live into SDD Flow. You see exactly what it did, step by step.',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
  },
];

export default function RemoteWorkersSection() {
  return (
    <section id="remote-workers" className="scroll-mt-14 py-20 px-4 sm:py-24 lg:py-32">
      <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">

        {/* Header */}
        <div className="text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5 text-sm font-medium text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            Always-on AI agents
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
            Let your machines do the work
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
            Remote Workers are background agents that run on your infrastructure and pick up jobs from SDD Flow automatically.
            Assign a Change Request, walk away — it's done when you get back.
          </p>
        </div>

        {/* Steps + mock terminal */}
        <div className="mt-16 grid gap-12 lg:grid-cols-2 lg:gap-16 lg:items-start">

          {/* Steps */}
          <div className="space-y-8">
            {steps.map((step) => (
              <div key={step.number} className="flex gap-5">
                <div className="flex-shrink-0 font-mono text-3xl font-bold text-slate-200 dark:text-slate-700 select-none">
                  {step.number}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{step.title}</h3>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{step.description}</p>
                  {step.code && (
                    <div className="mt-3 flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5">
                      <span className="text-slate-500 select-none">$</span>
                      <code className="font-mono text-sm text-emerald-400">{step.code}</code>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Mock worker dashboard card */}
          <div className="rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-800 overflow-hidden">
            <div className="border-b border-slate-100 px-5 py-3 dark:border-slate-700">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Connected Workers</p>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-700">
              {[
                { name: 'dev-macbook', agent: 'claude', status: 'busy', job: 'Applying CR: add dark mode' },
                { name: 'ci-server', agent: 'claude', status: 'online', job: null },
                { name: 'staging-box', agent: 'claude', status: 'online', job: null },
              ].map((w) => (
                <div key={w.name} className="flex items-center justify-between px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
                        <svg className="h-4 w-4 text-slate-500 dark:text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0H3" />
                        </svg>
                      </div>
                      <span className={`absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white dark:border-slate-800 ${w.status === 'busy' ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-white">{w.name}</p>
                      {w.job ? (
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[180px]">{w.job}</p>
                      ) : (
                        <p className="text-xs text-slate-400 dark:text-slate-500">Waiting for jobs…</p>
                      )}
                    </div>
                  </div>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    w.status === 'busy'
                      ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                      : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                  }`}>
                    {w.status}
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t border-slate-100 bg-slate-50 px-5 py-3 dark:border-slate-700 dark:bg-slate-900/40">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                1 job running · 2 workers idle · last activity 12s ago
              </div>
            </div>
          </div>
        </div>

        {/* Benefits grid */}
        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((b) => (
            <div key={b.title} className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-800">
              <div className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${b.bg} ${b.color}`}>
                {b.icon}
              </div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{b.title}</h3>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{b.description}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
