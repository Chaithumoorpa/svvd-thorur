/**
 * Decode JWT token (frontend only, no verification)
 * Browser-safe implementation
 */
export function decodeToken(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = parts[1];

    // Browser-safe base64 decode
    const decodedPayload = JSON.parse(
      decodeURIComponent(
        atob(payload)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
    );

    return decodedPayload;
  } catch (error) {
    console.error('Failed to decode token:', error);
    return null;
  }
}

/**
 * Get token from localStorage
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('token');
}

/**
 * Check if user has admin role (ADMIN or SUPER_ADMIN)
 */
export function isUserAdmin(): boolean {
  const token = getToken();
  if (!token) return false;

  const decoded = decodeToken(token);
  if (!decoded) return false;

  // Backward compatibility
  if (decoded.is_admin === true || decoded.isAdmin === true) {
    return true;
  }

  const roles: string[] = decoded.roles || [];
  return roles.includes('ADMIN') || roles.includes('SUPER_ADMIN');
}

/**
 * Check if user has super admin role
 */
export function isUserSuperAdmin(): boolean {
  const token = getToken();
  if (!token) return false;

  const decoded = decodeToken(token);
  if (!decoded) return false;

  return (decoded.roles || []).includes('SUPER_ADMIN');
}

/**
 * Check if user has trustee role
 */
export function isUserTrustee(): boolean {
  const token = getToken();
  if (!token) return false;

  const decoded = decodeToken(token);
  if (!decoded) return false;

  const roles: string[] = decoded.roles || [];
  return roles.includes('TRUSTEE') || roles.includes('ADMIN') || roles.includes('SUPER_ADMIN');
}

/**
 * Verify token with backend (STRICT check)
 */
export async function verifyTokenStatus(): Promise<{
  isAuthenticated: boolean;
  roles: string[];
  isAdmin: boolean;
  isSuperAdmin: boolean;
  isTrustee: boolean;
  mustChangePassword: boolean;
  username?: string;
  lastLogin?: string;
}> {
  const token = getToken();

  if (!token) {
    return {
      isAuthenticated: false,
      roles: [],
      isAdmin: false,
      isSuperAdmin: false,
      isTrustee: false,
      mustChangePassword: false,
    };
  }

  try {
    const { api } = await import('@/lib/api');
    const res = await api.get('/auth/verify');

    return {
      isAuthenticated: true,
      roles: res.data.roles || [],
      isAdmin: res.data.is_admin === true,
      isSuperAdmin: res.data.is_super_admin === true,
      isTrustee: res.data.is_trustee === true,
      mustChangePassword: res.data.must_change_password === true,
      username: res.data.username,
      lastLogin: res.data.last_login,
    };
  } catch (error) {
    console.error('Token verification failed:', error);
    localStorage.removeItem('token');

    return {
      isAuthenticated: false,
      roles: [],
      isAdmin: false,
      isSuperAdmin: false,
      isTrustee: false,
      mustChangePassword: false,
    };
  }
}
