'use client';

import { authManager } from '@/lib/auth';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import NotificationCenter from './NotificationCenter';
import SearchBar from './SearchBar';
import ThemeToggle from './ThemeToggle';

export default function Navigation() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const navRef = useRef<HTMLDivElement>(null);

  // Check if we're on a public agent page
  const isPublicAgentPage = pathname?.startsWith('/agent/') && !pathname.includes('/dashboard');

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

  // Handle click outside to close mobile menu and user dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
        setIsUserDropdownOpen(false);
      }
    };

    if (isMenuOpen || isUserDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isMenuOpen, isUserDropdownOpen]);

  const handleLogout = async () => {
    await authManager.logout();
    router.push('/login');
  };

  return (
    <nav className="bg-white dark:bg-gray-900 shadow-lg border-b border-gray-200 dark:border-gray-700" ref={navRef}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl font-bold text-gray-900 dark:text-white">PropertyAI</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
              Home
            </Link>
            <div className="w-64">
              <SearchBar />
            </div>
            <NotificationCenter />
            <ThemeToggle />

            {isAuthenticated && !isPublicAgentPage ? (
              <>
                <Link href="/dashboard" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Dashboard
                </Link>
                <Link href="/dashboard?section=properties" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Properties
                </Link>
                <Link href="/dashboard?section=posts" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Posts
                </Link>
                <Link href="/dashboard?section=profile" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Profile
                </Link>
                <div className="relative">
                  <button
                    onClick={() => setIsUserDropdownOpen(!isUserDropdownOpen)}
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium flex items-center focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                  >
                    {user?.firstName || 'User'} ▼
                  </button>
                  {isUserDropdownOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50 border border-gray-200 dark:border-gray-700">
                      <button
                        onClick={() => {
                          handleLogout();
                          setIsUserDropdownOpen(false);
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white transition-colors focus:outline-none focus:bg-gray-100 dark:focus:bg-gray-700"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : !isPublicAgentPage ? (
              <>
                <Link href="/login" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                  Login
                </Link>
                <Link href="/register" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                  Register
                </Link>
              </>
            ) : null}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white p-3 rounded-md transition-colors min-h-[48px] min-w-[48px] flex items-center justify-center"
              aria-label="Toggle mobile menu"
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
            <div className="px-4 pt-4 pb-4 space-y-2 bg-gray-50 dark:bg-gray-800 rounded-md mt-2 border border-gray-200 dark:border-gray-700">
              <Link
                href="/"
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block px-4 py-4 rounded-md text-base font-medium transition-colors touch-manipulation min-h-[48px] flex items-center"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </Link>
              <div className="px-4 py-3">
                <SearchBar />
              </div>
              <div className="px-4 py-3">
                <NotificationCenter />
              </div>
              <div className="px-4 py-3">
                <ThemeToggle />
              </div>

              {isAuthenticated && !isPublicAgentPage ? (
                <>
                  <Link
                    href="/dashboard"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/dashboard?section=properties"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Properties
                  </Link>
                  <Link
                    href="/dashboard?section=posts"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Posts
                  </Link>
                  <Link
                    href="/dashboard?section=profile"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                    onClick={() => setIsMenuOpen(false)}
                  >
                    Profile
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setIsMenuOpen(false);
                    }}
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block w-full text-left px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
                  >
                    Logout
                  </button>
                </>
              ) : !isPublicAgentPage ? (
                <>
                  <Link
                    href="/login"
                    className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white block px-4 py-3 rounded-md text-base font-medium transition-colors touch-manipulation"
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
              ) : null}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}