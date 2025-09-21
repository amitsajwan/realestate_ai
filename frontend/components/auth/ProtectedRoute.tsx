'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { simpleAuth, AuthUser } from '@/lib/simple-auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

/**
 * Protected Route Component
 * ========================
 * Wraps components that require authentication
 */
export default function ProtectedRoute({ 
  children, 
  redirectTo = '/simple-login' 
}: ProtectedRouteProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Check if user is authenticated
        const authenticated = simpleAuth.isAuthenticated();
        
        if (authenticated) {
          // Verify token is still valid by getting current user
          const currentUser = await simpleAuth.getCurrentUser();
          
          if (currentUser) {
            setIsAuthenticated(true);
            setUser(currentUser);
          } else {
            // Token is invalid, redirect to login
            simpleAuth.clearAuthState();
            router.push(redirectTo);
          }
        } else {
          // Not authenticated, redirect to login
          router.push(redirectTo);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        simpleAuth.clearAuthState();
        router.push(redirectTo);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router, redirectTo]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  return <>{children}</>;
}