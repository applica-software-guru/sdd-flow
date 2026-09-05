import TenantSwitcher from '@/components/tenant-switcher';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import Navigation from './navigation';

interface MobileNavigationProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenantId?: string;
  projectId?: string;
  projectName?: string;
  isAdmin: boolean;
}
export default function MobileNavigation(props: MobileNavigationProps) {
  return (
    <Dialog open={props.open} onOpenChange={props.onOpenChange}>
      <DialogContent className="inset-y-0 left-0 top-0 h-screen w-72 max-w-[85vw] translate-x-0 translate-y-0 rounded-none p-0 lg:hidden">
        <DialogHeader className="border-b pr-12">
          <DialogTitle>SDD Flow</DialogTitle>
          <DialogDescription className="sr-only">Application navigation</DialogDescription>
        </DialogHeader>
        <div className="border-b p-3">
          <TenantSwitcher />
        </div>
        <div className="overflow-y-auto p-3">
          {props.projectName && (
            <div className="mb-3 rounded-md bg-muted px-3 py-2">
              <p className="text-xs font-medium text-muted-foreground">Current project</p>
              <p className="truncate text-sm font-semibold">{props.projectName}</p>
            </div>
          )}
          <Navigation
            tenantId={props.tenantId}
            projectId={props.projectId}
            projectName={props.projectName}
            isAdmin={props.isAdmin}
            onNavigate={() => props.onOpenChange(false)}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
