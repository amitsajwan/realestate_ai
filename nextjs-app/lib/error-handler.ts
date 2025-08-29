'use client';

import toast from 'react-hot-toast';

export interface AppError {
  code: string;
  message: string;
  details?: any;
  statusCode?: number;
}

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorMap: Map<string, string> = new Map();

  constructor() {
    this.initializeErrorMap();
  }

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  private initializeErrorMap(): void {
    // Authentication errors
    this.errorMap.set('INVALID_CREDENTIALS', 'Invalid email or password');
    this.errorMap.set('USER_NOT_FOUND', 'User account not found');
    this.errorMap.set('EMAIL_ALREADY_EXISTS', 'An account with this email already exists');
    this.errorMap.set('TOKEN_EXPIRED', 'Your session has expired. Please log in again');
    this.errorMap.set('UNAUTHORIZED', 'You are not authorized to perform this action');
    
    // Onboarding errors
    this.errorMap.set('ONBOARDING_STEP_INVALID', 'Invalid onboarding step');
    this.errorMap.set('ONBOARDING_DATA_MISSING', 'Required onboarding information is missing');
    this.errorMap.set('BRANDING_GENERATION_FAILED', 'Failed to generate branding suggestions');
    
    // Network errors
    this.errorMap.set('NETWORK_ERROR', 'Network connection error. Please check your internet connection');
    this.errorMap.set('SERVER_ERROR', 'Server error. Please try again later');
    this.errorMap.set('TIMEOUT_ERROR', 'Request timed out. Please try again');
    
    // Validation errors
    this.errorMap.set('VALIDATION_ERROR', 'Please check your input and try again');
    this.errorMap.set('REQUIRED_FIELD_MISSING', 'Please fill in all required fields');
    
    // Generic errors
    this.errorMap.set('UNKNOWN_ERROR', 'An unexpected error occurred. Please try again');
  }

  /**
   * Handle and display errors with appropriate user feedback
   */
  handleError(error: any, context?: string): AppError {
    const appError = this.parseError(error, context);
    
    // Log error for debugging
    console.error(`[ErrorHandler] ${context || 'Unknown context'}:`, {
      code: appError.code,
      message: appError.message,
      details: appError.details,
      originalError: error
    });

    // Show user-friendly toast notification
    this.showErrorToast(appError);

    return appError;
  }

  /**
   * Parse various error formats into standardized AppError
   */
  private parseError(error: any, context?: string): AppError {
    // Handle API response errors
    if (error?.response) {
      const { status, data } = error.response;
      const errorCode = data?.code || data?.error || this.getErrorCodeFromStatus(status);
      const errorMessage = data?.detail || data?.message || this.errorMap.get(errorCode) || 'An error occurred';
      
      return {
        code: errorCode,
        message: errorMessage,
        statusCode: status,
        details: data
      };
    }

    // Handle network errors
    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
      return {
        code: 'NETWORK_ERROR',
        message: this.errorMap.get('NETWORK_ERROR') || 'Network error',
        details: error
      };
    }

    // Handle timeout errors
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      return {
        code: 'TIMEOUT_ERROR',
        message: this.errorMap.get('TIMEOUT_ERROR') || 'Request timed out',
        details: error
      };
    }

    // Handle custom app errors
    if (error?.code && this.errorMap.has(error.code)) {
      return {
        code: error.code,
        message: this.errorMap.get(error.code) || error.message,
        details: error.details
      };
    }

    // Handle generic errors
    return {
      code: 'UNKNOWN_ERROR',
      message: error?.message || this.errorMap.get('UNKNOWN_ERROR') || 'An unexpected error occurred',
      details: error
    };
  }

  /**
   * Map HTTP status codes to error codes
   */
  private getErrorCodeFromStatus(status: number): string {
    switch (status) {
      case 400:
        return 'VALIDATION_ERROR';
      case 401:
        return 'UNAUTHORIZED';
      case 403:
        return 'FORBIDDEN';
      case 404:
        return 'NOT_FOUND';
      case 409:
        return 'CONFLICT';
      case 422:
        return 'VALIDATION_ERROR';
      case 429:
        return 'RATE_LIMIT_EXCEEDED';
      case 500:
        return 'SERVER_ERROR';
      case 502:
      case 503:
      case 504:
        return 'SERVICE_UNAVAILABLE';
      default:
        return 'UNKNOWN_ERROR';
    }
  }

  /**
   * Show error toast notification
   */
  private showErrorToast(error: AppError): void {
    toast.error(error.message, {
      duration: 5000,
      position: 'top-right',
      style: {
        background: '#ef4444',
        color: 'white',
        borderRadius: '8px',
        padding: '12px 16px'
      }
    });
  }

  /**
   * Show success toast notification
   */
  showSuccess(message: string): void {
    toast.success(message, {
      duration: 4000,
      position: 'top-right',
      style: {
        background: '#10b981',
        color: 'white',
        borderRadius: '8px',
        padding: '12px 16px'
      }
    });
  }

  /**
   * Show info toast notification
   */
  showInfo(message: string): void {
    toast(message, {
      duration: 4000,
      position: 'top-right',
      icon: 'ℹ️',
      style: {
        background: '#3b82f6',
        color: 'white',
        borderRadius: '8px',
        padding: '12px 16px'
      }
    });
  }

  /**
   * Handle async operations with error handling
   */
  async withErrorHandling<T>(
    operation: () => Promise<T>,
    context?: string,
    showSuccessMessage?: string
  ): Promise<{ data?: T; error?: AppError }> {
    try {
      const result = await operation();
      
      if (showSuccessMessage) {
        this.showSuccess(showSuccessMessage);
      }
      
      return { data: result };
    } catch (error) {
      const appError = this.handleError(error, context);
      return { error: appError };
    }
  }

  /**
   * Create a custom error
   */
  createError(code: string, message?: string, details?: any): AppError {
    return {
      code,
      message: message || this.errorMap.get(code) || 'An error occurred',
      details
    };
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();

// Export utility functions
export const handleError = (error: any, context?: string) => errorHandler.handleError(error, context);
export const showSuccess = (message: string) => errorHandler.showSuccess(message);
export const showInfo = (message: string) => errorHandler.showInfo(message);
export const withErrorHandling = <T>(
  operation: () => Promise<T>,
  context?: string,
  successMessage?: string
) => errorHandler.withErrorHandling(operation, context, successMessage);