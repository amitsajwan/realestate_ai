"use client";

import Onboarding from '@/components/Onboarding';
import { authManager, User } from '@/lib/auth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';

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

      if (state.user?.onboarding_completed) {
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
      // Show success message
      toast.success('Onboarding completed successfully! Redirecting to dashboard...');

      // Force a refresh of auth state before redirecting
      await authManager.init();
      console.log('[OnboardingPage] Auth state refreshed, redirecting to dashboard');

      // Check if user is now marked as onboarding completed
      const state = authManager.getState();
      console.log('[OnboardingPage] Current auth state after refresh:', {
        isAuthenticated: state.isAuthenticated,
        hasUser: !!state.user,
        onboarding_completed: state.user?.onboarding_completed,
        onboarding_step: state.user?.onboarding_step
      });

      // Always redirect to dashboard after onboarding completion
      // regardless of the onboarding_completed flag state
      console.log('[OnboardingPage] Redirecting to dashboard');

      // Use replace instead of push to prevent back navigation to onboarding
      router.replace('/dashboard');

    } catch (err) {
      console.error('[OnboardingPage] Error during redirect:', err);

      // Fallback to direct navigation if router fails
      console.log('[OnboardingPage] Router failed, using window.location for redirect');
      if (typeof window !== 'undefined') {
        window.location.href = '/dashboard';
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
