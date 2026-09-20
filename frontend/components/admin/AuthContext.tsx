'use client';

import { createContext, useContext } from 'react';
import type { Me, Permission } from '@/lib/types';

interface AuthValue {
  me: Me;
  /** UI convenience only - the backend re-checks every permission on every request. */
  can: (permission: Permission) => boolean;
}

export const AuthContext = createContext<AuthValue | null>(null);

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside the admin layout');
  return value;
}
