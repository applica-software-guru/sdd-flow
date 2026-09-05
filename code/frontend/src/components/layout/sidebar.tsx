import Navigation from './navigation';

interface SidebarProps {
  tenantId?: string;
  projectId?: string;
  projectName?: string;
  isAdmin: boolean;
  isSuperUser: boolean;
}
export default function Sidebar(props: SidebarProps) {
  return (
    <aside className="hidden w-56 shrink-0 overflow-y-auto border-r bg-card p-3 lg:block">
      <Navigation {...props} />
    </aside>
  );
}
