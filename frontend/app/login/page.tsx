'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'react-hot-toast';
import { Eye, EyeOff, Mail, Lock, User, Phone, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { authManager } from '@/lib/auth';
import { handleError, showSuccess, withErrorHandling } from '@/lib/error-handler';
import { LoginFormData, ValidationErrors, RegisterRequest } from '@/types/user'
import { useFormSubmission } from '@/hooks/useLoading'
import { LoadingButton } from '@/components/LoadingStates';
import { 
  loginSchema, 
  registerSchema, 
  validateForm, 
  validateField,
  calculatePasswordStrength,
  FormValidator,
  PasswordStrength
} from '@/lib/form-validation';

// Using unified types from @/types/user
// FormData and ValidationErrors are imported from the types file

const LoginPage: React.FC = () => {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
    firstName: '',
    lastName: '',
    phone: '',
    confirmPassword: ''
  });
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
    score: 0,
    feedback: [],
    color: 'bg-gray-200',
    label: 'Very Weak'
  });

  // Form validators
  const [loginValidator] = useState(() => new FormValidator(loginSchema));
  const [registerValidator] = useState(() => new FormValidator(registerSchema));
  
  const currentValidator = isLogin ? loginValidator : registerValidator;
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
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Validate field on change if it's been touched
    if (currentValidator.isTouched(name)) {
      currentValidator.validateField(name, value);
    }
  };

  const handleBlur = (field: string) => {
    currentValidator.touch(field);
    currentValidator.validateField(field, formData[field as keyof LoginFormData]);
  };

  const getFieldValidationIcon = (field: keyof LoginFormData) => {
    if (!isClient || !currentValidator.isTouched(field) || !formData[field]) return null;
    
    const hasError = currentValidator.hasFieldError(field);
    if (hasError) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
    return <CheckCircle className="w-5 h-5 text-green-500" />;
  };

  const isFormValid = () => {
    const validation = currentValidator.validateAll(formData);
    return validation;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate the form
    if (!currentValidator.validateAll(formData)) {
      toast.error('Please fix the validation errors before submitting');
      return;
    }

    await submit(async () => {
      if (isLogin) {
        const result = await authManager.login(formData.email, formData.password);
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
      } else {
        const registerData = {
          email: formData.email,
          password: formData.password,
          confirmPassword: formData.confirmPassword,
          firstName: formData.firstName || '',
          lastName: formData.lastName || '',
          phone: formData.phone || undefined
        };

         const result = await authManager.register(registerData);
        
        if (result.success) {
          setIsLogin(true);
          setFormData({
            email: formData.email,
            password: '',
            firstName: '',
            lastName: '',
            phone: '',
            confirmPassword: ''
          });
        }
      }
    }, {
      errorMessage: isLogin ? 'Login failed' : 'Registration failed'
    });
  };

  const handleFacebookLogin = async () => {
    await submit(async () => {
      const rawBase = (process.env.NEXT_PUBLIC_API_BASE_URL as string | undefined) ?? ''
      const base = (!rawBase || rawBase === 'undefined' || rawBase === 'null')
        ? ''
        : rawBase.replace(/\/+$/, '')
      const response = await fetch(`${base}/api/v1/auth/facebook/login`);
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
              onClick={() => {
                setIsLogin(!isLogin);
                currentValidator.reset();
                setFormData({
                  email: '',
                  password: '',
                  firstName: '',
                  lastName: '',
                  phone: '',
                  confirmPassword: ''
                });
              }}
              className="ml-1 font-medium text-indigo-600 hover:text-indigo-500 focus:outline-none focus:underline transition duration-150 ease-in-out hover-lift click-shrink min-h-[44px] inline-flex items-center"
            >
              {isLogin ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>

        <form className="mt-6 sm:mt-8 space-y-5 sm:space-y-6 animate-fade-in" onSubmit={handleSubmit}>
          <div className="space-y-4 sm:space-y-5">
            {/* Registration Fields */}
            {!isLogin && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="firstName" className="sr-only">
                      First Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <User className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        id="firstName"
                        name="firstName"
                        type="text"
                        autoComplete="given-name"
                        required={!isLogin}
                        className={`appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border ${
                          isClient && currentValidator.hasFieldError('firstName') ? 'border-red-300' : isClient && currentValidator.isFieldValid('firstName') ? 'border-green-300' : 'border-gray-300'
                        } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift`}
                        placeholder="First Name"
                        value={formData.firstName}
                        onChange={handleChange}
                        onBlur={() => handleBlur('firstName')}
                        aria-describedby={isClient && currentValidator.hasFieldError('firstName') ? 'firstName-error' : undefined}
                      />
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                        {getFieldValidationIcon('firstName')}
                      </div>
                    </div>
                    {isClient && currentValidator.hasFieldError('firstName') && (
                      <p id="firstName-error" className="mt-1 text-sm text-red-600" role="alert">
                        {currentValidator.getFieldError('firstName')}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="lastName" className="sr-only">
                      Last Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <User className="h-5 w-5 text-gray-400" />
                      </div>
                      <input
                        id="lastName"
                        name="lastName"
                        type="text"
                        autoComplete="family-name"
                        required={!isLogin}
                        className={`appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border ${
                          isClient && currentValidator.hasFieldError('lastName') ? 'border-red-300' : isClient && currentValidator.isFieldValid('lastName') ? 'border-green-300' : 'border-gray-300'
                        } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift`}
                        placeholder="Last Name"
                        value={formData.lastName}
                        onChange={handleChange}
                        onBlur={() => handleBlur('lastName')}
                        aria-describedby={isClient && currentValidator.hasFieldError('lastName') ? 'lastName-error' : undefined}
                      />
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                        {getFieldValidationIcon('lastName')}
                      </div>
                    </div>
                    {isClient && currentValidator.hasFieldError('lastName') && (
                      <p id="lastName-error" className="mt-1 text-sm text-red-600" role="alert">
                        {currentValidator.getFieldError('lastName')}
                      </p>
                    )}
                  </div>
                </div>

                <div>
                  <label htmlFor="phone" className="sr-only">
                    Phone Number
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Phone className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      id="phone"
                      name="phone"
                      type="tel"
                      autoComplete="tel"
                        className={`appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border ${
                        isClient && currentValidator.hasFieldError('phone') ? 'border-red-300' : isClient && currentValidator.isFieldValid('phone') && formData.phone ? 'border-green-300' : 'border-gray-300'
                        } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift`}
                      placeholder="Phone Number (Optional)"
                      value={formData.phone}
                      onChange={handleChange}
                      onBlur={() => handleBlur('phone')}
                      aria-describedby={isClient && currentValidator.hasFieldError('phone') ? 'phone-error' : undefined}
                    />
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                      {getFieldValidationIcon('phone')}
                    </div>
                  </div>
                    {isClient && currentValidator.hasFieldError('phone') && (
                      <p id="phone-error" className="mt-1 text-sm text-red-600" role="alert">
                        {currentValidator.getFieldError('phone')}
                      </p>
                    )}
                </div>
              </>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                    className={`appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border ${
                    isClient && currentValidator.hasFieldError('email') ? 'border-red-300' : isClient && currentValidator.isFieldValid('email') ? 'border-green-300' : 'border-gray-300'
                    } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift`}
                  placeholder="Email address"
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={() => handleBlur('email')}
                  aria-describedby={isClient && currentValidator.hasFieldError('email') ? 'email-error' : undefined}
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  {getFieldValidationIcon('email')}
                </div>
              </div>
                {isClient && currentValidator.hasFieldError('email') && (
                  <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">
                    {currentValidator.getFieldError('email')}
                  </p>
                )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  required
                    className={`appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border ${
                    isClient && currentValidator.hasFieldError('password') ? 'border-red-300' : isClient && currentValidator.isFieldValid('password') ? 'border-green-300' : 'border-gray-300'
                    } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift`}
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={() => handleBlur('password')}
                  aria-describedby={isClient && currentValidator.hasFieldError('password') ? 'password-error' : undefined}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center min-w-[44px] min-h-[44px] justify-center hover-glow click-shrink"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
                {isClient && currentValidator.hasFieldError('password') && (
                  <p id="password-error" className="mt-1 text-sm text-red-600" role="alert">
                    {currentValidator.getFieldError('password')}
                  </p>
                )}
              
              {/* Password Strength Indicator */}
              {!isLogin && formData.password && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg border animate-fade-in">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Password Strength:</span>
                    <span className={`text-sm font-semibold px-2 py-1 rounded-full text-xs ${
                      passwordStrength.score >= 4 ? 'text-green-700 bg-green-100' : 
                      passwordStrength.score >= 3 ? 'text-yellow-700 bg-yellow-100' : 'text-red-700 bg-red-100'
                    }`}>
                      {passwordStrength.label}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ease-out ${passwordStrength.color}`}
                      style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                    ></div>
                  </div>
                  {passwordStrength.feedback.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-gray-700 mb-1">Requirements:</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {passwordStrength.feedback.map((item, index) => (
                          <li key={index} className="flex items-center">
                            <span className="w-1 h-1 bg-gray-400 rounded-full mr-2"></span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Confirm Password Field */}
            {!isLogin && (
              <div>
                <label htmlFor="confirmPassword" className="sr-only">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    required={!isLogin}
                      className={`appearance-none relative block w-full px-3 py-3 sm:py-2 pl-10 pr-10 border ${
                      isClient && currentValidator.hasFieldError('confirmPassword') ? 'border-red-300' : isClient && currentValidator.isFieldValid('confirmPassword') ? 'border-green-300' : 'border-gray-300'
                      } placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 text-base sm:text-sm transition-all duration-200 hover-lift`}
                    placeholder="Confirm Password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    onBlur={() => handleBlur('confirmPassword')}
                    aria-describedby={isClient && currentValidator.hasFieldError('confirmPassword') ? 'confirmPassword-error' : undefined}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center min-w-[44px] min-h-[44px] justify-center hover-glow click-shrink"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
                    {isClient && currentValidator.hasFieldError('confirmPassword') && (
                      <p id="confirmPassword-error" className="mt-1 text-sm text-red-600" role="alert">
                        {currentValidator.getFieldError('confirmPassword')}
                      </p>
                    )}
              </div>
            )}
          </div>

          <div>
            <LoadingButton
              type="submit"
              isLoading={isLoading}
              disabled={!isFormValid()}
              className="group relative w-full flex justify-center py-3 sm:py-2 px-4 border border-transparent text-base sm:text-sm font-medium rounded-lg text-white min-h-[48px] bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 hover-lift click-shrink transition-all duration-200 ease-in-out"
            >
              {isLogin ? 'Sign in' : 'Create account'}
            </LoadingButton>
          </div>

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
        </form>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
