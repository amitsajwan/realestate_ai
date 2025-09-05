import { AuthManager } from '../../lib/auth';
import { APIService } from '../../lib/api';
import { errorHandler, handleError } from '../../lib/error-handler';
import { User } from '../../types/user';

// Mock the dependencies
jest.mock('../../lib/api');
jest.mock('../../lib/error-handler', () => ({
  errorHandler: {
    handleError: jest.fn((error, context) => ({
      code: 'MOCK_ERROR',
      message: `Mocked error: ${error.message} in ${context}`,
      originalError: error,
    })),
    showSuccess: jest.fn(),
    showInfo: jest.fn(),
    withErrorHandling: jest.fn(),
  },
  handleError: jest.fn((error, context) => ({
    code: 'MOCK_ERROR',
    message: `Mocked error: ${error.message} in ${context}`,
    originalError: error,
  })),
  showSuccess: jest.fn(),
}));

const mockAPIService = APIService as jest.MockedClass<typeof APIService>;

describe('AuthManager', () => {
  let authManager: AuthManager;
  let mockAPI: jest.Mocked<APIService>;

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    
    // Clear localStorage
    localStorage.clear();
    
    // Mock the APIService constructor to return our mock instance
    mockAPI = new (mockAPIService as any)();
    (APIService as jest.Mock).mockImplementation(() => mockAPI);

    // Create a new instance of AuthManager before each test
    authManager = new AuthManager();
    
    // Manually inject the mocked APIService into the new AuthManager instance
    (authManager as any).apiService = mockAPI;
    
    // Reset auth state to ensure clean test environment
    (authManager as any).state = {
      isAuthenticated: false,
      user: null,
      token: null,
      refreshToken: null,
      isLoading: false,
      error: null
    };
  });

  describe('login', () => {
    it('should login successfully and return user data', async () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        isVerified: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        onboardingCompleted: false,
        onboardingStep: 1
      };
      const mockResponse = { accessToken: 'fake-token', refreshToken: 'fake-refresh', user: mockUser };

      // Configure the mock implementation for the login method
  mockAPI.login.mockResolvedValue(mockResponse);

      const result = await authManager.login('test@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(authManager.getState().isAuthenticated).toBe(true);
      expect(authManager.getState().user).toEqual(mockUser);
      expect(mockAPI.login).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' });
    });

    it('should handle login failure', async () => {
      const errorMessage = 'Invalid credentials';
      mockAPI.login.mockRejectedValue(new Error(errorMessage));

      const result = await authManager.login('wrong@example.com', 'wrongpassword');

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(authManager.getState().isAuthenticated).toBe(false);
      expect(handleError).toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      // First, simulate a logged-in state
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        isVerified: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        onboardingCompleted: false,
        onboardingStep: 1
      };
      (authManager as any).setState({ isAuthenticated: true, user: mockUser, token: 'fake-token' });

  mockAPI.logout.mockResolvedValue({ message: 'Logged out' });

      await authManager.logout();

      expect(authManager.getState().isAuthenticated).toBe(false);
      expect(authManager.getState().user).toBeNull();
      expect(authManager.getState().token).toBeNull();
      expect(mockAPI.logout).toHaveBeenCalled();
    });
  });

  describe('register', () => {
    it('should register successfully and return user data', async () => {
      const registerData = {
        email: 'test@example.com',
        password: 'password123',
        confirmPassword: 'password123',
        firstName: 'Test',
        lastName: 'User',
        phone: '1234567890'
      };
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        isVerified: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        onboardingCompleted: false,
        onboardingStep: 1
      };
      const mockResponse = { accessToken: 'fake-token', refreshToken: 'fake-refresh', user: mockUser };

  mockAPI.register.mockResolvedValue(mockResponse);

  const result = await authManager.register(registerData);

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(authManager.getState().isAuthenticated).toBe(true);
      expect(authManager.getState().user).toEqual(mockUser);
      expect(mockAPI.register).toHaveBeenCalled();
    });

    it('should handle register failure', async () => {
      const registerData = {
        email: 'test@example.com',
        password: 'password123',
        confirmPassword: 'password123',
        firstName: 'Test',
        lastName: 'User',
        phone: '1234567890'
      };
      const errorMessage = 'Email already exists';
      mockAPI.register.mockRejectedValue(new Error(errorMessage));

      const result = await authManager.register(registerData);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(authManager.getState().isAuthenticated).toBe(false);
      expect(handleError).toHaveBeenCalled();
    });
  });

  describe('updateProfile', () => {
    it('should update profile successfully', async () => {
      const updatedUser: User = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Updated',
        lastName: 'Name',
        isVerified: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        onboardingCompleted: false,
        onboardingStep: 1
      };
  mockAPI.updateProfile.mockResolvedValue(updatedUser);

  const result = await authManager.updateProfile({ firstName: 'Updated', lastName: 'Name' });

      expect(result.success).toBe(true);
      expect(result.user).toEqual(updatedUser);
      expect(authManager.getState().user).toEqual(updatedUser);
  expect(mockAPI.updateProfile).toHaveBeenCalledWith({ firstName: 'Updated', lastName: 'Name' });
    });

    it('should handle profile update failure', async () => {
      const errorMessage = 'Update failed';
      mockAPI.updateProfile.mockRejectedValue(new Error(errorMessage));

      const result = await authManager.updateProfile({ firstName: 'Updated', lastName: 'Name' });

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('changePassword', () => {
    it('should change password successfully', async () => {
  mockAPI.changePassword.mockResolvedValue({ message: 'Password changed' });

      const result = await authManager.changePassword('oldPassword', 'newPassword');

      expect(result.success).toBe(true);
      expect(mockAPI.changePassword).toHaveBeenCalledWith({ current_password: 'oldPassword', new_password: 'newPassword' });
    });

    it('should handle password change failure', async () => {
      const errorMessage = 'Incorrect password';
      mockAPI.changePassword.mockRejectedValue(new Error(errorMessage));

      const result = await authManager.changePassword('wrongOldPassword', 'newPassword');

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('updateOnboarding', () => {
    it('should update onboarding successfully', async () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        isVerified: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        onboardingCompleted: false,
        onboardingStep: 1
      };
      (authManager as any).setState({ isAuthenticated: true, user: mockUser, token: 'fake-token' });

      mockAPI.updateOnboarding.mockResolvedValue({ success: true, data: { ...mockUser, onboardingStep: 2 } });

      const result = await authManager.updateOnboarding(2, { some: 'data' });

      expect(result).toBe(true);
      expect(authManager.getState().user?.onboardingStep).toBe(2);
      expect(mockAPI.updateOnboarding).toHaveBeenCalledWith('1', { step: 2, data: { some: 'data' }, completed: false });
    });

    it('should handle onboarding update failure', async () => {
      const mockUser: User = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        isVerified: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        onboardingCompleted: false,
        onboardingStep: 1
      };
      (authManager as any).setState({ isAuthenticated: true, user: mockUser, token: 'fake-token' });

      const errorMessage = 'Update failed';
      mockAPI.updateOnboarding.mockRejectedValue(new Error(errorMessage));

      const result = await authManager.updateOnboarding(2, { some: 'data' });

      expect(result).toBe(false);
      expect(handleError).toHaveBeenCalled();
    });
  });
});