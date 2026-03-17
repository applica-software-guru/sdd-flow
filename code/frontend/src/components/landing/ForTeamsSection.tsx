const benefits = [
  {
    title: 'Role-based access control',
    description: 'Owner, Admin, Member, and Viewer roles keep everyone in their lane.',
  },
  {
    title: 'Assignments & notifications',
    description: 'Assign CRs and bugs to team members. Get notified when things change.',
  },
  {
    title: 'Complete audit trail',
    description: 'Track every change, approval, and status transition across your organization.',
  },
  {
    title: 'Multi-tenant isolation',
    description: 'Each organization gets its own workspace with isolated projects and members.',
  },
];

export default function ForTeamsSection() {
  return (
    <section id="for-teams" className="scroll-mt-14 bg-slate-50 py-20 px-4 dark:bg-slate-800/50 sm:py-24 lg:py-32">
      <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Text side */}
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              Built for teams of all sizes
            </h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-400">
              From solo developers to large organizations, SDD Flow scales with your team and keeps everyone aligned.
            </p>
            <ul className="mt-8 space-y-5">
              {benefits.map((b) => (
                <li key={b.title} className="flex gap-3">
                  <div className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
                    <svg className="h-4 w-4 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-white">{b.title}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">{b.description}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Visual card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-700 dark:bg-slate-800">
            <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">Team Members</div>
            <div className="space-y-3">
              {[
                { name: 'Alice Chen', role: 'Owner', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
                { name: 'Bob Martinez', role: 'Admin', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
                { name: 'Carol Singh', role: 'Member', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
                { name: 'David Kim', role: 'Viewer', color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300' },
              ].map((member) => (
                <div key={member.name} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                      {member.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <span className="text-sm font-medium text-slate-900 dark:text-white">{member.name}</span>
                  </div>
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${member.color}`}>
                    {member.role}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
