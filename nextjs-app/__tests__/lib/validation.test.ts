import { validateEmail, validatePassword, validateName, validatePhone, validateConfirmPassword, validateRequired, sanitizeInput, getFieldError, getFieldErrorClass } from '@/lib/validation';
import { describe, it, expect } from '@jest/globals';

describe('Validation Utility Functions', () => {

  describe('validateEmail', () => {
    it('should return valid for a correct email', () => {
      const result = validateEmail('test@example.com');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for an incorrect email', () => {
      const result = validateEmail('invalid-email');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Please enter a valid email address');
    });
  });

  describe('validatePassword', () => {
    it('should return valid for a strong password', () => {
      const result = validatePassword('Password123!');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for a weak password', () => {
      const result = validatePassword('weak');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Password must be at least 8 characters long');
    });
  });

  describe('validateName', () => {
    it('should return valid for a correct name', () => {
      const result = validateName('John Doe');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for a name that is too short', () => {
      const result = validateName('J');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Name must be at least 2 characters long');
    });
  });

  describe('validatePhone', () => {
    it('should return valid for a correct phone number', () => {
      const result = validatePhone('1234567890');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid for a phone number that is too short', () => {
      const result = validatePhone('123');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Phone number must be at least 10 digits');
    });
  });

  describe('validateConfirmPassword', () => {
    it('should return valid if passwords match', () => {
      const result = validateConfirmPassword('password123', 'password123');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid if passwords do not match', () => {
      const result = validateConfirmPassword('password123', 'wrongpassword');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Passwords do not match');
    });
  });

  describe('validateRequired', () => {
    it('should return valid if value is present', () => {
      const result = validateRequired('some value', 'Field');
      expect(result.isValid).toBe(true);
    });

    it('should return invalid if value is empty', () => {
      const result = validateRequired('', 'Field');
      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Field is required');
    });
  });

  describe('sanitizeInput', () => {
    it('should sanitize HTML characters', () => {
      const input = '<script>alert("xss")</script>';
      const sanitized = sanitizeInput(input);
      expect(sanitized).toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;&#x2F;script&gt;');
    });
  });

  describe('getFieldError', () => {
    it('should return the error message for a field', () => {
      const errors = { name: { message: 'Name is required' } };
      const message = getFieldError(errors, 'name');
      expect(message).toBe('Name is required');
    });
  });

  describe('getFieldErrorClass', () => {
    it('should return the error class if field has an error', () => {
      const errors = { name: { message: 'Name is required' } };
      const className = getFieldErrorClass(errors, 'name');
      expect(className).toBe('border-red-500');
    });

    it('should return an empty string if field has no error', () => {
      const errors = {};
      const className = getFieldErrorClass(errors, 'name');
      expect(className).toBe('');
    });
  });

});