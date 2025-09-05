/**
 * Custom hooks for consistent loading state management
 * Provides unified loading patterns across all components
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { handleError, showSuccess } from '@/lib/error-handler';

// Loading state interface
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
  success: string | null;
}

// Options for async operations
export interface AsyncOperationOptions {
  successMessage?: string;
  errorMessage?: string;
  showSuccessToast?: boolean;
  showErrorToast?: boolean;
  resetAfter?: number; // Reset state after X milliseconds
}

/**
 * Basic loading state hook
 * Provides simple loading, error, and success state management
 */
export const useLoading = (initialLoading: boolean = false) => {
  const [state, setState] = useState<LoadingState>({
    isLoading: initialLoading,
    error: null,
    success: null
  });

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading, error: null, success: null }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, isLoading: false, success: null }));
  }, []);

  const setSuccess = useCallback((success: string | null) => {
    setState(prev => ({ ...prev, success, isLoading: false, error: null }));
  }, []);

  const reset = useCallback(() => {
    setState({ isLoading: false, error: null, success: null });
  }, []);

  return {
    ...state,
    setLoading,
    setError,
    setSuccess,
    reset
  };
};

/**
 * Advanced async operation hook
 * Handles async operations with automatic loading states and error handling
 */
export const useAsyncOperation = <T = any>() => {
  const [state, setState] = useState<LoadingState & { data: T | null }>({
    isLoading: false,
    error: null,
    success: null,
    data: null
  });

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Clear timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const execute = useCallback(async <R = T>(
    operation: () => Promise<R>,
    options: AsyncOperationOptions = {}
  ): Promise<R | null> => {
    const {
      successMessage,
      errorMessage = 'Operation failed',
      showSuccessToast = true,
      showErrorToast = true,
      resetAfter = 3000
    } = options;

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null, success: null }));
      
      const result = await operation();
      
      const successMsg = successMessage || 'Operation completed successfully';
      setState(prev => ({
        ...prev,
        isLoading: false,
        success: successMsg,
        data: result as T,
        error: null
      }));

      if (showSuccessToast && successMessage) {
        showSuccess(successMsg);
      }

      // Auto-reset after specified time
      if (resetAfter > 0) {
        timeoutRef.current = setTimeout(() => {
          setState(prev => ({ ...prev, success: null, error: null }));
        }, resetAfter);
      }

      return result;
    } catch (error: any) {
      console.error('Async operation failed:', error);
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        success: null
      }));

      if (showErrorToast) {
        handleError(error, errorMessage);
      }

      return null;
    }
  }, []);

  const reset = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setState({ isLoading: false, error: null, success: null, data: null });
  }, []);

  return {
    ...state,
    execute,
    reset
  };
};

/**
 * Multiple operations loading hook
 * Manages loading states for multiple concurrent operations
 */
export const useMultipleLoading = () => {
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const setLoading = useCallback((key: string, loading: boolean) => {
    setLoadingStates(prev => ({ ...prev, [key]: loading }));
    if (loading) {
      setErrors(prev => ({ ...prev, [key]: null }));
    }
  }, []);

  const setError = useCallback((key: string, error: string | null) => {
    setErrors(prev => ({ ...prev, [key]: error }));
    setLoadingStates(prev => ({ ...prev, [key]: false }));
  }, []);

  const isLoading = useCallback((key?: string) => {
    if (key) {
      return loadingStates[key] || false;
    }
    return Object.values(loadingStates).some(loading => loading);
  }, [loadingStates]);

  const getError = useCallback((key: string) => {
    return errors[key] || null;
  }, [errors]);

  const reset = useCallback((key?: string) => {
    if (key) {
      setLoadingStates(prev => ({ ...prev, [key]: false }));
      setErrors(prev => ({ ...prev, [key]: null }));
    } else {
      setLoadingStates({});
      setErrors({});
    }
  }, []);

  return {
    setLoading,
    setError,
    isLoading,
    getError,
    reset,
    loadingStates,
    errors
  };
};

/**
 * Form submission hook
 * Specialized hook for form submissions with validation and loading states
 */
export const useFormSubmission = <T = any>() => {
  const [state, setState] = useState<LoadingState & { 
    isSubmitting: boolean;
    validationErrors: Record<string, string>;
  }>({
    isLoading: false,
    isSubmitting: false,
    error: null,
    success: null,
    validationErrors: {}
  });

  const submit = useCallback(async (
    submitFn: () => Promise<T>,
    options: AsyncOperationOptions & {
      validateFn?: () => Record<string, string> | null;
    } = {}
  ): Promise<T | null> => {
    const { validateFn, ...asyncOptions } = options;

    try {
      // Run validation if provided
      if (validateFn) {
        const validationErrors = validateFn();
        if (validationErrors && Object.keys(validationErrors).length > 0) {
          setState(prev => ({
            ...prev,
            validationErrors,
            error: 'Please fix the validation errors',
            isSubmitting: false
          }));
          return null;
        }
      }

      setState(prev => ({
        ...prev,
        isSubmitting: true,
        isLoading: true,
        error: null,
        success: null,
        validationErrors: {}
      }));

      const result = await submitFn();

      const successMsg = asyncOptions.successMessage || 'Form submitted successfully';
      setState(prev => ({
        ...prev,
        isSubmitting: false,
        isLoading: false,
        success: successMsg,
        error: null
      }));

      if (asyncOptions.showSuccessToast !== false) {
        showSuccess(successMsg);
      }

      return result;
    } catch (error: any) {
      console.error('Form submission failed:', error);
      
      const errorMsg = asyncOptions.errorMessage || 'Form submission failed';
      setState(prev => ({
        ...prev,
        isSubmitting: false,
        isLoading: false,
        error: errorMsg,
        success: null
      }));

      if (asyncOptions.showErrorToast !== false) {
        handleError(error, errorMsg);
      }

      return null;
    }
  }, []);

  const setValidationErrors = useCallback((errors: Record<string, string>) => {
    setState(prev => ({ ...prev, validationErrors: errors }));
  }, []);

  const clearValidationError = useCallback((field: string) => {
    setState(prev => ({
      ...prev,
      validationErrors: {
        ...prev.validationErrors,
        [field]: ''
      }
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      isLoading: false,
      isSubmitting: false,
      error: null,
      success: null,
      validationErrors: {}
    });
  }, []);

  return {
    ...state,
    submit,
    setValidationErrors,
    clearValidationError,
    reset
  };
};

/**
 * Debounced loading hook
 * Prevents rapid loading state changes
 */
export const useDebouncedLoading = (delay: number = 300) => {
  const [isLoading, setIsLoading] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const setLoading = useCallback((loading: boolean) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    if (loading) {
      // Show loading immediately
      setIsLoading(true);
    } else {
      // Delay hiding loading to prevent flicker
      timeoutRef.current = setTimeout(() => {
        setIsLoading(false);
      }, delay);
    }
  }, [delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return { isLoading, setLoading };
};