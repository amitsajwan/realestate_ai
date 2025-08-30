"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authManager } from '@/lib/auth';
import { User } from '@/types/user';
import Onboarding from '@/components/Onboarding';

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

  const handleOnboardingComplete = () => {
    console.log('[OnboardingPage] Onboarding completed, redirecting to dashboard');
    // Force a refresh of auth state before redirecting
    authManager.init().then(() => {
      console.log('[OnboardingPage] Auth state refreshed, redirecting to dashboard');
      // Use replace instead of push to prevent back navigation to onboarding
      router.replace('/dashboard');
    }).catch(err => {
      console.error('[OnboardingPage] Error refreshing auth state:', err);
      // Fallback to direct navigation if refresh fails
      window.location.href = '/dashboard';
    });
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
