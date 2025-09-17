/**
 * Error Handling System
 * =====================
 * Centralized error handling for the application
 */

export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: any
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: any) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication required') {
    super(message, 'AUTHENTICATION_ERROR', 401);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'Insufficient permissions') {
    super(message, 'AUTHORIZATION_ERROR', 403);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string = 'Resource') {
    super(`${resource} not found`, 'NOT_FOUND_ERROR', 404);
    this.name = 'NotFoundError';
  }
}

export class NetworkError extends AppError {
  constructor(message: string = 'Network error occurred') {
    super(message, 'NETWORK_ERROR', 0);
    this.name = 'NetworkError';
  }
}

export class APIError extends AppError {
  constructor(
    message: string,
    statusCode: number,
    public response?: any
  ) {
    super(message, 'API_ERROR', statusCode, response);
    this.name = 'APIError';
  }
}

// Error handler utility
export function handleError(error: unknown): AppError {
  if (error instanceof AppError) {
    return error;
  }

  if (error instanceof Error) {
    return new AppError(error.message, 'UNKNOWN_ERROR', 500);
  }

  return new AppError('An unknown error occurred', 'UNKNOWN_ERROR', 500);
}

// Error logging utility
export function logError(error: AppError, context?: string) {
  console.error(`[${error.name}] ${context ? `[${context}] ` : ''}${error.message}`, {
    code: error.code,
    statusCode: error.statusCode,
    details: error.details,
    stack: error.stack
  });
}

// Error boundary helper
export function isError(error: unknown): error is AppError {
  return error instanceof AppError;
}

// Error message formatter
export function formatErrorMessage(error: AppError): string {
  switch (error.code) {
    case 'VALIDATION_ERROR':
      return `Validation failed: ${error.message}`;
    case 'AUTHENTICATION_ERROR':
      return 'Please log in to continue';
    case 'AUTHORIZATION_ERROR':
      return 'You do not have permission to perform this action';
    case 'NOT_FOUND_ERROR':
      return error.message;
    case 'NETWORK_ERROR':
      return 'Please check your internet connection and try again';
    case 'API_ERROR':
      return `Server error: ${error.message}`;
    default:
      return error.message || 'An unexpected error occurred';
  }
}