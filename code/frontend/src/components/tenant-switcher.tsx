import { Building2, Check, ChevronsUpDown, Plus } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useTenants } from '@/hooks/use-tenants';

export default function TenantSwitcher() {
  const navigate = useNavigate();
  const { tenantId } = useParams();
  const { data: tenants } = useTenants();
  const current = tenants?.find((tenant) => tenant.id === tenantId);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="max-w-56 justify-between">
          <Building2 aria-hidden="true" />
          <span className="truncate">{current?.name || 'Select tenant'}</span>
          <ChevronsUpDown className="ml-auto opacity-50" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {tenants?.map((tenant) => (
          <DropdownMenuItem key={tenant.id} onSelect={() => navigate(`/tenants/${tenant.id}`)}>
            {tenant.name}
            {tenant.id === tenantId && <Check className="ml-auto" aria-hidden="true" />}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate('/tenants/new')}>
          <Plus aria-hidden="true" />
          New tenant
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
