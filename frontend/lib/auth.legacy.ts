/**
 * Legacy Auth Manager - DEPRECATED
 * ================================
 * This file is kept for backward compatibility.
 * New code should use the auth module: import { authManager } from './auth'
 */

// Import from new auth module
import { authManager as newAuthManager, AuthManager as NewAuthManager } from './auth';
import type { AuthState, AuthResult, LoginData, RegisterData, User } from './auth';
import { useEffect, useState } from 'react';

// Re-export for backward compatibility
export const authManager = newAuthManager;
export const AuthManager = NewAuthManager;
export type { AuthState, AuthResult, LoginData, RegisterData, User };

// React hook for using auth state - DEPRECATED
// Use the new auth module instead: import { authManager } from './auth'
export function useAuth() {
  const [state, setState] = useState(authManager.getState());

  useEffect(() => {
    const unsubscribe = authManager.subscribe(setState);
    return unsubscribe;
  }, []);

  return {
    ...state,
    login: authManager.login.bind(authManager),
    register: authManager.register.bind(authManager),
    logout: authManager.logout.bind(authManager)
  };
}
