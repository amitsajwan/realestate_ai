"use client";

import Onboarding from '@/components/Onboarding';
import { authManager } from '@/lib/auth';
import { User } from '@/types/user';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function OnboardingPage() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      await authManager.init();
      const state = authManager.getState();

      console.log('[OnboardingPage] Auth state:', {
        isAuthenticated: state.isAuthenticated,
        user: state.user
      });

      if (!state.isAuthenticated) {
        router.push('/login');
        return;
      }

      if (state.user?.onboardingCompleted) {
        router.push('/dashboard');
        return;
      }

      setUser(state.user);
      setIsLoading(false);
    };

    initAuth();
  }, [router]);

  const handleStepChange = (step: number) => {
    setCurrentStep(step);
  };

  const handleOnboardingComplete = async () => {
    console.log('[OnboardingPage] Onboarding completed, redirecting to dashboard');
    try {
      // Force a refresh of auth state before redirecting
      await authManager.init();
      console.log('[OnboardingPage] Auth state refreshed, redirecting to dashboard');

      // Check if user is now marked as onboarding completed
      const state = authManager.getState();
      console.log('[OnboardingPage] Current auth state after refresh:', {
        isAuthenticated: state.isAuthenticated,
        hasUser: !!state.user,
        onboardingCompleted: state.user?.onboardingCompleted,
        onboardingStep: state.user?.onboardingStep
      });

      if (state.user?.onboardingCompleted) {
        console.log('[OnboardingPage] User onboarding confirmed as completed, redirecting to dashboard');
        // Use replace instead of push to prevent back navigation to onboarding
        router.replace('/dashboard');
      } else {
        console.warn('[OnboardingPage] User onboarding not marked as completed, forcing redirect');
        console.log('[OnboardingPage] User object:', state.user);
        // Fallback to direct navigation if state is inconsistent
        if (typeof window !== 'undefined') {
          console.log('[OnboardingPage] Using window.location.href for redirect');
          window.location.href = '/dashboard';
        } else {
          console.log('[OnboardingPage] Using router.replace for redirect');
          router.replace('/dashboard');
        }
      }
    } catch (err) {
      console.error('[OnboardingPage] Error refreshing auth state:', err);
      // Fallback to direct navigation if refresh fails
      if (typeof window !== 'undefined') {
        console.log('[OnboardingPage] Error fallback: Using window.location.href for redirect');
        window.location.href = '/dashboard';
      } else {
        console.log('[OnboardingPage] Error fallback: Using router.replace for redirect');
        router.replace('/dashboard');
      }
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <Onboarding
      user={user}
      currentStep={currentStep}
      onStepChange={handleStepChange}
      onComplete={handleOnboardingComplete}
    />
  );
}
