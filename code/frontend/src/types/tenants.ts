export interface Tenant {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface TenantMember {
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
}

export interface TenantInvitation {
  id: string;
  tenant_id: string;
  email: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  status: 'pending' | 'accepted' | 'expired';
}
