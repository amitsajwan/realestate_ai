'use client';

import { LoadingButton } from '@/components/LoadingStates';
import LoginForm from '@/components/auth/LoginForm';
import RegisterForm from '@/components/auth/RegisterForm';
import { useFormSubmission } from '@/hooks/useLoading';
import { authManager } from '@/lib/auth';
import { handleError, showSuccess } from '@/lib/error-handler';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import React, { useEffect, useRef, useState } from 'react';
import { toast } from 'react-hot-toast';

// Using unified types from @/types/user
// FormData and ValidationErrors are imported from the types file

const LoginPage: React.FC = () => {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const { submit, isLoading } = useFormSubmission();

  // Check if user is already authenticated
  const isInitialMount = useRef(true);
  const [isClient, setIsClient] = useState(false);

  const handleFacebookCallback = async (accessToken: string, refreshToken: string) => {
    try {
      // Only run client-side code
      if (typeof window !== 'undefined') {
        // Store tokens in localStorage to be picked up by authManager
        localStorage.setItem('authState', JSON.stringify({ accessToken, refreshToken }));

        // Clear URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
      }

      // Initialize auth state
      await authManager.init();
      const authState = authManager.getState();

      // Show success message
      showSuccess('Successfully logged in with Facebook!');

      // Redirect to dashboard or onboarding
      if (authState.user?.onboardingCompleted) {
        router.push('/dashboard');
      } else {
        router.push('/onboarding');
      }
    } catch (error) {
      handleError(error, 'Facebook login failed.');
    }
  };

  useEffect(() => {
    // Set client flag after hydration
    setIsClient(true);

    // Skip the authentication check on the initial server-side render
    // This prevents hydration mismatch between server and client
    if (isInitialMount.current) {
      isInitialMount.current = false;

      // Only run client-side code after hydration
      if (typeof window !== 'undefined') {
        // Check for Facebook authentication callback
        const urlParams = new URLSearchParams(window.location.search);
        const accessToken = urlParams.get('access_token');
        const refreshToken = urlParams.get('refresh_token');
        const facebookLogin = urlParams.get('facebook_login');

        if (accessToken && refreshToken && facebookLogin === 'true') {
          // Handle Facebook authentication callback
          handleFacebookCallback(accessToken, refreshToken);
          return;
        }
      }
    }

    const checkAuth = async () => {
      try {
        const isAuthenticated = await authManager.isAuthenticated();
        if (isAuthenticated) {
          router.push('/dashboard');
        }
      } catch (error) {
        console.error('[LoginPage] Auth check failed:', error);
      }
    };
    checkAuth();
  }, [router]);

  const handleLogin = async (email: string, password: string) => {
    const result = await authManager.login(email, password);
    if (result.success) {
      // Wait for auth state to be fully updated before redirecting
      await authManager.init();
      const authState = authManager.getState();

      // Check onboarding status and redirect accordingly
      if (authState.user?.onboardingCompleted) {
        router.push('/dashboard');
      } else {
        router.push('/onboarding');
      }
    }
  };

  const handleRegister = async (registerData: any) => {
    // The registerData is already in the correct format for RegisterData
    const result = await authManager.register(registerData);

    if (result.success) {
      setIsLogin(true);
      toast.success('Registration successful! Please sign in.');
    }
  };

  const handleSwitchMode = () => {
    setIsLogin(!isLogin);
  };

  const handleFacebookLogin = async () => {
    await submit(async () => {
      const rawBase = (process.env.NEXT_PUBLIC_API_BASE_URL as string | undefined) ?? ''
      const base = (!rawBase || rawBase === 'undefined' || rawBase === 'null')
        ? ''
        : rawBase.replace(/\/+$/, '')
      const response = await fetch(`${base}/api/v1/facebook/login`);
      const data = await response.json();

      if (data.auth_url && typeof window !== 'undefined') {
        window.location.href = data.auth_url;
      } else {
        toast.error('Facebook login is not available');
      }
    }, {
      errorMessage: 'Facebook login failed'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-100 flex items-center justify-center py-6 px-4 sm:py-12 sm:px-6 lg:px-8 animate-fade-in">
      <div className="max-w-md w-full space-y-6 sm:space-y-8">
        <div className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl backdrop-blur-lg border border-white/20 animate-slide-up">
          <div className="text-center">
            <h2 className="mt-4 sm:mt-6 text-2xl sm:text-3xl font-extrabold text-gray-900 leading-tight">
              {isLogin ? 'Sign in to your account' : 'Create your account'}
            </h2>
            <p className="mt-3 sm:mt-2 text-sm text-gray-600 leading-relaxed">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
              <br className="sm:hidden" />
              <button
                type="button"
                onClick={handleSwitchMode}
                className="ml-1 font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:underline transition duration-150 ease-in-out hover-lift click-shrink min-h-[44px] inline-flex items-center"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>

          {/* Render appropriate form based on mode */}
          {isLogin ? (
            <LoginForm onSubmit={handleLogin} isLoading={isLoading} />
          ) : (
            <RegisterForm onSubmit={handleRegister} onSwitchToLogin={handleSwitchMode} isLoading={isLoading} />
          )}

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or continue with</span>
              </div>
            </div>

            <div className="mt-6">
              <LoadingButton
                type="button"
                onClick={handleFacebookLogin}
                isLoading={isLoading}
                className="w-full inline-flex justify-center py-3 sm:py-2 px-4 border border-gray-300 rounded-lg shadow-sm bg-white text-base sm:text-sm font-medium text-gray-500 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 ease-in-out hover-lift click-shrink min-h-[48px]"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#1877F2"
                    d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
                  />
                </svg>
                <span className="ml-2">Facebook</span>
              </LoadingButton>
            </div>
          </div>

          {isLogin && (
            <div className="text-center">
              <Link
                href="/forgot-password"
                className="text-sm text-indigo-600 hover:text-indigo-500 focus:outline-none focus:underline transition duration-150 ease-in-out hover-lift click-shrink min-h-[44px] inline-flex items-center justify-center"
              >
                Forgot your password?
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
