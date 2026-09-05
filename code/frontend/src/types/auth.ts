export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  email_verified: boolean;
  has_password?: boolean;
  google_linked?: boolean;
  platform_role: 'user' | 'super_user';
  created_at: string;
  updated_at?: string;
}

export interface UserBrief {
  id: string;
  display_name: string;
  email: string;
  avatar_url?: string | null;
}
