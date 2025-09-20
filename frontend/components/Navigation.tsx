'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useRef } from 'react';
import { authManager } from '@/lib/auth';

export default function Navigation() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const router = useRouter();
  const navRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const initAuth = async () => {
      await authManager.init();
      const state = authManager.getState();
      setIsAuthenticated(state.isAuthenticated);
      setUser(state.user);
    };
    
    initAuth();
    
    // Subscribe to auth state changes
    const unsubscribe = authManager.subscribe((state) => {
      setIsAuthenticated(state.isAuthenticated);
      setUser(state.user);
    });
    
    return unsubscribe;
  }, []);

  // Handle click outside to close mobile menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isMenuOpen]);

  const handleLogout = async () => {
    await authManager.logout();
    router.push('/');
  };

  return (
    <nav className="bg-gray-900 shadow-lg" ref={navRef}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl font-bold text-white">PropertyAI</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
              Home
            </Link>

            {isAuthenticated ? (
              <>
                <Link href="/dashboard" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </Link>
                <Link href="/properties" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Properties
                </Link>
                <Link href="/posts" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Posts
                </Link>
                <Link href="/profile" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Profile
                </Link>
                <div className="relative group">
                  <button className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium flex items-center">
                    {user?.firstName || 'User'} ▼
                  </button>
                  <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-md shadow-lg py-1 z-50 hidden group-hover:block">
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <Link href="/login" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                  Login
                </Link>
                <Link href="/register" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                  Register
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-300 hover:text-white p-2 rounded-md"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-800 rounded-md mt-2">
              <Link 
                href="/" 
                className="text-gray-300 hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </Link>

              {isAuthenticated ? (
                <>
                  <Link 
                    href="/dashboard" 
                    className="text-gray-300 hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  <Link 
                    href="/properties" 
                    className="text-gray-300 hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Properties
                  </Link>
                  <Link 
                    href="/posts" 
                    className="text-gray-300 hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Posts
                  </Link>
                  <Link 
                    href="/profile" 
                    className="text-gray-300 hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Profile
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setIsMenuOpen(false);
                    }}
                    className="text-gray-300 hover:text-white block w-full text-left px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link 
                    href="/login" 
                    className="text-gray-300 hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Login
                  </Link>
                  <Link 
                    href="/register" 
                    className="bg-blue-600 hover:bg-blue-700 text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}