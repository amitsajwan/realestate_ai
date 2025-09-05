import { ErrorHandler, AppError, errorHandler, handleError, showSuccess, showInfo, withErrorHandling } from '../../lib/error-handler'
import toast from 'react-hot-toast'

// Mock react-hot-toast
jest.mock('react-hot-toast', () => {
  const toast = jest.fn();
  (toast as any).error = jest.fn();
  (toast as any).success = jest.fn();
  return toast;
});

const mockToast = toast as jest.MockedFunction<typeof toast>;

describe('ErrorHandler', () => {
  let errorHandlerInstance: ErrorHandler
  
  beforeEach(() => {
    jest.clearAllMocks()
    // Suppress console.error for tests
    jest.spyOn(console, 'error').mockImplementation(() => {})
    errorHandlerInstance = ErrorHandler.getInstance()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  describe('Singleton Pattern', () => {
    it('should return the same instance', () => {
      const instance1 = ErrorHandler.getInstance()
      const instance2 = ErrorHandler.getInstance()
      expect(instance1).toBe(instance2)
    })

    it('should export the singleton instance', () => {
      expect(errorHandler).toBeInstanceOf(ErrorHandler)
      expect(errorHandler).toBe(ErrorHandler.getInstance())
    })
  })

  describe('Error Parsing', () => {
    it('should parse API response errors correctly', () => {
      const apiError = {
        response: {
          status: 400,
          data: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input data',
            detail: 'Email is required'
          }
        }
      }

      const result = errorHandlerInstance.handleError(apiError, 'API Test')

      expect(result).toEqual({
        code: 'VALIDATION_ERROR',
        message: 'Email is required',
        statusCode: 400,
        details: apiError.response.data
      })
    })

    it('should handle array error messages', () => {
      const apiError = {
        response: {
          status: 422,
          data: {
            message: ['Email is required', 'Password is too short']
          }
        }
      }

      const result = errorHandlerInstance.handleError(apiError)

      expect(result.message).toBe('Email is required, Password is too short')
    })

    it('should handle object error messages', () => {
      const apiError = {
        response: {
          status: 400,
          data: {
            message: { email: 'Invalid format', password: 'Too weak' }
          }
        }
      }

      const result = errorHandlerInstance.handleError(apiError)

      expect(result.message).toBe('{"email":"Invalid format","password":"Too weak"}')
    })

    it('should parse network errors', () => {
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'Network Error'
      }

      const result = errorHandlerInstance.handleError(networkError)

      expect(result).toEqual({
        code: 'NETWORK_ERROR',
        message: 'Network connection error. Please check your internet connection',
        details: networkError
      })
    })

    it('should parse timeout errors', () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      }

      const result = errorHandlerInstance.handleError(timeoutError)

      expect(result).toEqual({
        code: 'TIMEOUT_ERROR',
        message: 'Request timed out. Please try again',
        details: timeoutError
      })
    })

    it('should handle custom app errors', () => {
      const customError = {
        code: 'USER_NOT_FOUND',
        message: 'Custom message',
        details: { userId: 123 }
      }

      const result = errorHandlerInstance.handleError(customError)

      expect(result).toEqual({
        code: 'USER_NOT_FOUND',
        message: 'User account not found',
        details: { userId: 123 }
      })
    })

    it('should handle generic errors', () => {
      const genericError = new Error('Something went wrong')

      const result = errorHandlerInstance.handleError(genericError)

      expect(result).toEqual({
        code: 'UNKNOWN_ERROR',
        message: 'Something went wrong',
        details: genericError
      })
    })

    it('should handle null/undefined errors', () => {
      const result = errorHandlerInstance.handleError(null)

      expect(result).toEqual({
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred. Please try again',
        details: null
      })
    })
  })

  describe('HTTP Status Code Mapping', () => {
    const statusCodeTests = [
      { status: 400, expectedCode: 'VALIDATION_ERROR' },
      { status: 401, expectedCode: 'UNAUTHORIZED' },
      { status: 403, expectedCode: 'FORBIDDEN' },
      { status: 404, expectedCode: 'NOT_FOUND' },
      { status: 409, expectedCode: 'CONFLICT' },
      { status: 422, expectedCode: 'VALIDATION_ERROR' },
      { status: 429, expectedCode: 'RATE_LIMIT_EXCEEDED' },
      { status: 500, expectedCode: 'SERVER_ERROR' },
      { status: 502, expectedCode: 'SERVICE_UNAVAILABLE' },
      { status: 503, expectedCode: 'SERVICE_UNAVAILABLE' },
      { status: 504, expectedCode: 'SERVICE_UNAVAILABLE' },
      { status: 999, expectedCode: 'UNKNOWN_ERROR' }
    ]

    statusCodeTests.forEach(({ status, expectedCode }) => {
      it(`should map status ${status} to ${expectedCode}`, () => {
        const apiError = {
          response: {
            status,
            data: {}
          }
        }

        const result = errorHandlerInstance.handleError(apiError)
        expect(result.code).toBe(expectedCode)
      })
    })
  })

  describe('Toast Notifications', () => {
    it('should show error toast when handling errors', () => {
      const error = new Error('Test error')
      
      errorHandlerInstance.handleError(error)

      expect(mockToast.error).toHaveBeenCalledWith(
        'Test error',
        expect.any(Object)
      )
    })

    it('should show success toast', () => {
      showSuccess('Success!')
      expect(mockToast.success).toHaveBeenCalledWith('Success!', expect.any(Object))
    })

    it('should show info toast', () => {
      showInfo('Information')
      expect(mockToast).toHaveBeenCalledWith('Information', expect.any(Object))
    })
  })

  describe('withErrorHandling', () => {
    it('should handle successful operations', async () => {
      const successfulOperation = jest.fn().mockResolvedValue('success result')
      
      const result = await errorHandlerInstance.withErrorHandling(
        successfulOperation,
        'Test Context',
        'Operation completed'
      )

      expect(result).toEqual({ data: 'success result' })
      expect(successfulOperation).toHaveBeenCalled()
      expect(mockToast.success).toHaveBeenCalledWith(
        'Operation completed',
        expect.any(Object)
      )
    })

    it('should handle failed operations', async () => {
      const failedOperation = jest.fn().mockRejectedValue(new Error('Operation failed'))
      
      const result = await errorHandlerInstance.withErrorHandling(
        failedOperation,
        'Test Context'
      )

      expect(result).toEqual({
        error: expect.objectContaining({
          code: 'UNKNOWN_ERROR',
          message: 'Operation failed'
        })
      })
      expect(failedOperation).toHaveBeenCalled()
      expect(mockToast.error).toHaveBeenCalled()
    })

    it('should not show success message when not provided', async () => {
      const successfulOperation = jest.fn().mockResolvedValue('success result')
      
      await errorHandlerInstance.withErrorHandling(successfulOperation)

      expect(mockToast.success).not.toHaveBeenCalled()
    })
  })

  describe('withErrorHandling HOC', () => {
    it('should return data on successful operation', async () => {
      const successfulOperation = jest.fn().mockResolvedValue('Success Data')
      const result = await withErrorHandling(successfulOperation, 'Test Op')

      expect(successfulOperation).toHaveBeenCalled()
      expect(result.data).toBe('Success Data')
      expect(result.error).toBeUndefined()
    })

    it('should show success message on successful operation', async () => {
      const successfulOperation = jest.fn().mockResolvedValue('Success Data')
      await withErrorHandling(successfulOperation, 'Test Op', 'It worked!')

      expect(mockToast.success).toHaveBeenCalledWith('It worked!', expect.any(Object))
    })

    it('should return error on failed operation', async () => {
      const error = new Error('Operation Failed')
      const failedOperation = jest.fn().mockRejectedValue(error)
      const result = await withErrorHandling(failedOperation, 'Test Op')

      expect(failedOperation).toHaveBeenCalled()
      expect(result.data).toBeUndefined()
      expect(result.error).toBeDefined()
      expect(result.error?.message).toBe('Operation Failed')
      expect(mockToast.error).toHaveBeenCalledWith('Operation Failed', expect.any(Object))
    })
  })

  describe('createError', () => {
    it('should create a custom error with a mapped message', () => {
      const error = errorHandlerInstance.createError('USER_NOT_FOUND')
      expect(error).toEqual({
        code: 'USER_NOT_FOUND',
        message: 'User account not found',
        details: undefined
      })
    })

    it('should create a custom error with a provided message', () => {
      const error = errorHandlerInstance.createError('CUSTOM_CODE', 'My custom message', { a: 1 })
      expect(error).toEqual({
        code: 'CUSTOM_CODE',
        message: 'My custom message',
        details: { a: 1 }
      })
    })
  })
  describe('Logging', () => {
    it('should log errors with context', () => {
      const consoleSpy = jest.spyOn(console, 'error')
      const error = new Error('Test error')
      
      errorHandlerInstance.handleError(error, 'Test Context')

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ErrorHandler] Test Context:',
        expect.objectContaining({
          code: 'UNKNOWN_ERROR',
          message: 'Test error',
          originalError: error
        })
      )
    })

    it('should log errors without context', () => {
      const consoleSpy = jest.spyOn(console, 'error')
      const error = new Error('Test error')
      
      errorHandlerInstance.handleError(error)

      expect(consoleSpy).toHaveBeenCalledWith(
        '[ErrorHandler] Unknown context:',
        expect.any(Object)
      )
    })
  })

  describe('Exported Utility Functions', () => {
    it('should export handleError function', () => {
      const error = new Error('Test error')
      const result = handleError(error, 'Test Context')
      
      expect(result).toEqual(
        expect.objectContaining({
          code: 'UNKNOWN_ERROR',
          message: 'Test error'
        })
      )
    })

    it('should export showSuccess function', () => {
      showSuccess('Success message')
      expect(mockToast.success).toHaveBeenCalledWith(
        'Success message',
        expect.any(Object)
      )
    })

    it('should export showInfo function', () => {
      showInfo('Info message')
      expect(mockToast).toHaveBeenCalledWith(
        'Info message',
        expect.any(Object)
      )
    })

    it('should export withErrorHandling function', async () => {
      const operation = jest.fn().mockResolvedValue('result')
      const result = await withErrorHandling(operation, 'Context', 'Success')
      
      expect(result).toEqual({ data: 'result' })
      expect(mockToast.success).toHaveBeenCalledWith('Success', expect.any(Object))
    })
  })

  describe('Error Map Initialization', () => {
    it('should initialize with predefined error messages', () => {
      const testCases = [
        { code: 'INVALID_CREDENTIALS', expectedMessage: 'Invalid email or password' },
        { code: 'USER_NOT_FOUND', expectedMessage: 'User account not found' },
        { code: 'EMAIL_ALREADY_EXISTS', expectedMessage: 'An account with this email already exists' },
        { code: 'TOKEN_EXPIRED', expectedMessage: 'Your session has expired. Please log in again' },
        { code: 'UNAUTHORIZED', expectedMessage: 'You are not authorized to perform this action' },
        { code: 'NETWORK_ERROR', expectedMessage: 'Network connection error. Please check your internet connection' },
        { code: 'SERVER_ERROR', expectedMessage: 'Server error. Please try again later' },
        { code: 'VALIDATION_ERROR', expectedMessage: 'Please check your input and try again' }
      ]

      testCases.forEach(({ code, expectedMessage }) => {
        const error = errorHandlerInstance.createError(code)
        expect(error.message).toBe(expectedMessage)
      })
    })
  })
})